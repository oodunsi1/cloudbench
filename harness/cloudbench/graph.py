from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

# Terraform resource type prefix -> provider-agnostic service family.
_TF_RESOURCE_MAP = {
    "aws_instance": "compute",
    "aws_launch_template": "compute",
    "aws_autoscaling_group": "compute",
    "aws_security_group": "security_group",
    "aws_iam_role": "iam_role",
    "aws_iam_instance_profile": "iam_instance_profile",
    "aws_s3_bucket": "s3",
    "aws_db_instance": "rds",
    "aws_rds_cluster": "rds",
    "aws_elasticache_cluster": "cache",
    "aws_lb": "alb",
    "aws_alb": "alb",
    "aws_lambda_function": "lambda",
    "aws_sqs_queue": "sqs",
    "aws_sns_topic": "sns",
}

_TF_RESOURCE_RE = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"')


def families_from_archspec(archspec: Dict[str, Any]) -> Set[str]:
    fams: Set[str] = set()
    for comp in archspec.get("components") or []:
        if isinstance(comp, dict):
            for key in ("service_family", "type"):
                v = comp.get(key)
                if isinstance(v, str) and v:
                    fams.add(v.strip().lower())
    for dep in archspec.get("stateful_deps") or []:
        if isinstance(dep, dict):
            v = dep.get("type")
            if isinstance(v, str) and v:
                fams.add(v.strip().lower())
    return fams


def families_from_terraform(terraform_dir: Path) -> Set[str]:
    fams: Set[str] = set()
    for tf in sorted(terraform_dir.glob("*.tf")):
        text = tf.read_text(encoding="utf-8", errors="replace")
        for match in _TF_RESOURCE_RE.finditer(text):
            rtype = match.group(1)
            mapped = _TF_RESOURCE_MAP.get(rtype)
            if mapped:
                fams.add(mapped)
    return fams


def graph_match_score(expected: Iterable[str], observed: Set[str]) -> Dict[str, Any]:
    """Fraction of expected service families present in observed set."""
    exp = {x.strip().lower() for x in expected}
    if not exp:
        return {"score": 0.0, "missing": [], "extra": sorted(observed), "matched": []}
    matched = exp & observed
    missing = sorted(exp - observed)
    extra = sorted(observed - exp)
    score = len(matched) / len(exp)
    return {
        "score": round(score, 4),
        "missing": missing,
        "extra": extra,
        "matched": sorted(matched),
    }


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
