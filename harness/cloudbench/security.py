"""Artifact-tier security lint — a free, no-cloud check of generated Terraform for insecure patterns.

This is the L1 security dimension: it never deploys anything, just reads the .tf text (the same
regex/heuristic stance as graph.py — no HCL parser dependency) and flags common, high-signal
misconfigurations. It is dependency-free by default; if the `checkov` CLI happens to be installed it
can be used instead for a deeper scan, but the built-in rules always run so a scan is always possible.

A case opts in via its `security_contract` (see SCHEMA.md). With no contract, the scan is advisory
(reported, never fails a case). With `fail_on_critical: true` or a `min_pass_rate`, the harness can
gate on it. Each finding is {rule_id, severity, resource, message}; severities: critical|high|medium|low.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

_SEVERITIES = ("critical", "high", "medium", "low")

# Ports that should essentially never be open to the whole internet.
_SENSITIVE_PORTS = {22: "SSH", 3389: "RDP", 3306: "MySQL", 5432: "PostgreSQL",
                    6379: "Redis", 27017: "MongoDB", 9200: "Elasticsearch", 5984: "CouchDB"}

_RESOURCE_HEADER_RE = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{')
# A literal AWS access key id in source is always wrong.
_AWS_KEY_RE = re.compile(r'\bAKIA[0-9A-Z]{16}\b')
# password = "literal" / secret = "literal" (not a var/ref/interpolation).
_HARDCODED_SECRET_RE = re.compile(
    r'\b(password|secret|secret_key|private_key)\s*=\s*"(?!\$\{|var\.|data\.|local\.)([^"]{4,})"',
    re.IGNORECASE,
)


@dataclass
class Finding:
    rule_id: str
    severity: str
    resource: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SecurityResult:
    scanner: str = "builtin"              # "builtin" | "checkov"
    findings: List[Dict[str, Any]] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)   # severity -> count
    pass_rate: float = 1.0                # 1 - (weighted findings / checks); 1.0 = clean
    passed: Optional[bool] = None         # vs the case's security_contract, if any (else None)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _iter_resource_blocks(text: str) -> Iterator[Tuple[str, str, str]]:
    """Yield (resource_type, name, body) for each resource block, body via brace matching."""
    for m in _RESOURCE_HEADER_RE.finditer(text):
        rtype, rname = m.group(1), m.group(2)
        depth, i, n = 1, m.end(), len(text)
        while i < n and depth:
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            i += 1
        yield rtype, rname, text[m.end():i - 1]


def _open_to_world(body: str) -> bool:
    return "0.0.0.0/0" in body or "::/0" in body


def _ports_in(body: str) -> List[int]:
    out: List[int] = []
    for fld in ("from_port", "to_port"):
        for mm in re.finditer(fld + r"\s*=\s*(\d+)", body):
            out.append(int(mm.group(1)))
    return out


def _sg_rules(rtype: str, body: str) -> List[str]:
    """The individual rule bodies to check — one per ingress/egress sub-block for an
    aws_security_group, or the whole body for a standalone aws_security_group_rule. Per-rule so a
    properly-restricted DB rule is not blamed for a sibling public app-port rule in the same group
    (the whole-block check used to false-positive on that)."""
    if rtype == "aws_security_group_rule":
        return [body]
    rules: List[str] = []
    for m in re.finditer(r"\b(?:ingress|egress)\s*\{", body):
        depth, i, n = 1, m.end(), len(body)
        while i < n and depth:
            if body[i] == "{":
                depth += 1
            elif body[i] == "}":
                depth -= 1
            i += 1
        rules.append(body[m.end():i - 1])
    return rules or [body]


def scan_builtin(terraform_dir: Path) -> List[Finding]:
    """Run the built-in rule set over every .tf file in the dir."""
    findings: List[Finding] = []
    for tf in sorted(Path(terraform_dir).glob("*.tf")):
        text = tf.read_text(encoding="utf-8", errors="replace")

        # Global (whole-file) rules.
        if _AWS_KEY_RE.search(text):
            findings.append(Finding("hardcoded-aws-key", "critical", tf.name,
                                    "A literal AWS access key id (AKIA...) is committed in Terraform."))
        for mm in _HARDCODED_SECRET_RE.finditer(text):
            findings.append(Finding("hardcoded-secret", "critical", tf.name,
                                    f"A '{mm.group(1).lower()}' is set to a hardcoded literal; use a variable or secret store."))

        # Per-resource rules.
        for rtype, rname, body in _iter_resource_blocks(text):
            ref = f"{rtype}.{rname}"
            if rtype in ("aws_security_group", "aws_security_group_rule"):
                open_rules = [r for r in _sg_rules(rtype, body) if _open_to_world(r)]
                if open_rules:
                    sens = sorted({p for r in open_rules for p in _ports_in(r) if p in _SENSITIVE_PORTS})
                    if sens:
                        names = ", ".join(f"{p} ({_SENSITIVE_PORTS[p]})" for p in sens)
                        findings.append(Finding("open-sensitive-port", "critical", ref,
                                                f"Security group opens sensitive port(s) {names} to 0.0.0.0/0."))
                    else:
                        findings.append(Finding("open-ingress", "high", ref,
                                                "Security group allows ingress from 0.0.0.0/0 (the whole internet)."))
            if rtype == "aws_s3_bucket" and re.search(r'acl\s*=\s*"public-read', body):
                findings.append(Finding("public-s3-bucket", "high", ref,
                                        "S3 bucket ACL is public-read/public-read-write."))
            if rtype == "aws_db_instance" and "storage_encrypted" not in body:
                findings.append(Finding("unencrypted-rds", "medium", ref,
                                        "RDS instance does not set storage_encrypted = true."))
            if rtype in ("aws_iam_policy", "aws_iam_role_policy") and re.search(r'"Action"\s*:\s*"\*"', body):
                findings.append(Finding("iam-wildcard-action", "high", ref,
                                        'IAM policy grants Action "*" (full privileges).'))
            if rtype == "aws_instance" and re.search(r'associate_public_ip_address\s*=\s*true', body):
                findings.append(Finding("public-instance-ip", "low", ref,
                                        "EC2 instance is given a public IP (associate_public_ip_address = true)."))
    return findings


def scan_checkov(terraform_dir: Path) -> Optional[List[Finding]]:
    """Use the checkov CLI if it is installed; return None if it is not available."""
    if shutil.which("checkov") is None:
        return None
    try:
        r = subprocess.run(["checkov", "-d", str(terraform_dir), "-o", "json", "--compact"],
                           capture_output=True, text=True, timeout=120)
        data = json.loads(r.stdout or "{}")
        results = (data.get("results") or {}) if isinstance(data, dict) else {}
        out: List[Finding] = []
        for chk in results.get("failed_checks", []) or []:
            out.append(Finding(chk.get("check_id", "checkov"), "high",
                               chk.get("resource", "?"), chk.get("check_name", "checkov finding")))
        return out
    except Exception:
        return None


def _weight(sev: str) -> float:
    return {"critical": 1.0, "high": 0.6, "medium": 0.3, "low": 0.1}.get(sev, 0.1)


def scan_terraform(terraform_dir: Path, *, prefer_checkov: bool = False) -> SecurityResult:
    """Scan a Terraform dir and summarise. Built-in by default; checkov only if asked AND installed."""
    scanner = "builtin"
    findings = None
    if prefer_checkov:
        findings = scan_checkov(terraform_dir)
        scanner = "checkov" if findings is not None else "builtin"
    if findings is None:
        findings = scan_builtin(terraform_dir)
    counts = {s: sum(1 for f in findings if f.severity == s) for s in _SEVERITIES}
    # pass_rate: 1.0 when clean; each finding subtracts its severity weight (floored at 0).
    penalty = sum(_weight(f.severity) for f in findings)
    pass_rate = max(0.0, 1.0 - penalty / 5.0)
    return SecurityResult(
        scanner=scanner,
        findings=[f.to_dict() for f in findings],
        counts=counts,
        pass_rate=round(pass_rate, 4),
    )


def evaluate_contract(result: SecurityResult, security_contract: Optional[dict]) -> SecurityResult:
    """Set result.passed against the case's security_contract (if any): fail_on_critical and/or
    min_pass_rate. With no contract, passed stays None (advisory only)."""
    if not security_contract:
        return result
    ok = True
    if security_contract.get("fail_on_critical") and result.counts.get("critical", 0) > 0:
        ok = False
    min_pr = security_contract.get("min_pass_rate")
    if isinstance(min_pr, (int, float)) and result.pass_rate < float(min_pr):
        ok = False
    result.passed = ok
    return result
