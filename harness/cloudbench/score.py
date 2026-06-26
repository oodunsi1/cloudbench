from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from cloudbench.graph import (
    families_from_archspec,
    families_from_terraform,
    graph_match_score,
    load_json,
)
from cloudbench.security import evaluate_contract, scan_terraform
from cloudbench.validate_ext import validate_cloudbench_case


@dataclass
class L1ScoreResult:
    case_id: str
    tier: str = "L1"
    passed: bool = False
    repospec_valid: Optional[bool] = None
    terraform_validate_ok: Optional[bool] = None
    graph_match: Dict[str, Any] = field(default_factory=dict)
    observed_families: List[str] = field(default_factory=list)
    security: Optional[Dict[str, Any]] = None  # artifact-tier security lint (advisory, or gated by contract)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _validate_repospec(repospec_path: Path) -> tuple[bool, List[str]]:
    errors: List[str] = []
    if not repospec_path.exists():
        return False, [f"RepoSpec not found: {repospec_path}"]
    try:
        from repospec_generator.schema import validate_repospec

        data = load_json(repospec_path)
        validate_repospec(data)
        return True, []
    except ImportError:
        return True, []  # optional: paper2 analyst not on path
    except Exception as e:
        errors.append(f"RepoSpec validation failed: {e}")
        return False, errors


def _terraform_validate(terraform_dir: Path) -> tuple[Optional[bool], List[str]]:
    if not terraform_dir.is_dir():
        return None, [f"Terraform dir not found: {terraform_dir}"]
    tf_files = list(terraform_dir.glob("*.tf"))
    if not tf_files:
        return False, ["No .tf files in terraform dir"]
    try:
        r = subprocess.run(
            ["terraform", "validate", "-no-color"],
            cwd=str(terraform_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if r.returncode == 0:
            return True, []
        msg = (r.stderr or r.stdout or "terraform validate failed").strip()
        return False, [msg[:2000]]
    except FileNotFoundError:
        return None, ["terraform not in PATH; skipped validate"]
    except subprocess.TimeoutExpired:
        return False, ["terraform validate timed out"]


def score_l1(
    case: dict,
    *,
    repospec_path: Optional[Path] = None,
    archspec_path: Optional[Path] = None,
    terraform_dir: Optional[Path] = None,
    skip_terraform_validate: bool = False,
    run_security: bool = True,
) -> L1ScoreResult:
    """Score a run at L1 — artifact tier, no cloud apply.

    Also runs the free security lint when Terraform is present (``run_security``): advisory by default,
    but a case's ``security_contract`` can make a critical finding fail the case.
    """
    validate_cloudbench_case(case, require_pinned=False)
    result = L1ScoreResult(case_id=case["id"])

    if repospec_path is not None:
        ok, errs = _validate_repospec(repospec_path)
        result.repospec_valid = ok
        result.errors.extend(errs)

    observed: set = set()
    if archspec_path and archspec_path.exists():
        try:
            observed |= families_from_archspec(load_json(archspec_path))
        except Exception as e:
            result.errors.append(f"ArchSpec read failed: {e}")

    if terraform_dir and terraform_dir.is_dir():
        observed |= families_from_terraform(terraform_dir)
        if not skip_terraform_validate:
            tv_ok, tv_errs = _terraform_validate(terraform_dir)
            result.terraform_validate_ok = tv_ok
            result.errors.extend(tv_errs)
        if run_security:
            sec = evaluate_contract(scan_terraform(terraform_dir), case.get("security_contract"))
            result.security = sec.to_dict()

    result.observed_families = sorted(observed)
    result.graph_match = graph_match_score(case["expected_service_families"], observed)
    result.passed = (
        result.graph_match.get("score", 0) >= 1.0
        and (result.repospec_valid is not False)
        and (result.terraform_validate_ok is not False)
        and (result.security is None or result.security.get("passed") is not False)
        and not any("not found" in e.lower() for e in result.errors)
    )
    return result


@dataclass
class L2ScoreResult:
    """L2 (plan) tier: terraform plan succeeds. Read-only — no resources are created — but the AWS
    provider still needs credentials to plan, so it is gated. ``passed=None`` means "not run"
    (no credentials / no terraform), distinct from passed=False ("plan failed")."""
    case_id: str
    tier: str = "L2"
    passed: Optional[bool] = None
    plan_ok: Optional[bool] = None
    skipped_reason: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _has_aws_credentials() -> bool:
    return any(os.environ.get(k) for k in ("AWS_ACCESS_KEY_ID", "AWS_PROFILE", "AWS_SESSION_TOKEN"))


def score_l2(case: dict, terraform_dir: Optional[Path], *, allow_cloud: bool = False) -> L2ScoreResult:
    """Score a run at L2 — terraform plan succeeds. Read-only, but gated on AWS credentials because
    the provider must initialise. Without credentials (and without --allow-cloud) it is skipped, not
    failed, so L2 never blocks an offline run."""
    validate_cloudbench_case(case, require_pinned=False)
    result = L2ScoreResult(case_id=case["id"])
    if not terraform_dir or not Path(terraform_dir).is_dir():
        result.passed = False
        result.errors.append(f"Terraform dir not found: {terraform_dir}")
        return result
    if not (allow_cloud or _has_aws_credentials()):
        result.skipped_reason = "L2 plan needs AWS credentials (read-only); pass --allow-cloud or set AWS_* to run"
        return result
    try:
        init = subprocess.run(["terraform", "init", "-input=false", "-no-color"],
                              cwd=str(terraform_dir), capture_output=True, text=True, timeout=180)
        if init.returncode != 0:
            result.plan_ok = False
            result.passed = False
            result.errors.append((init.stderr or init.stdout or "terraform init failed").strip()[:2000])
            return result
        plan = subprocess.run(["terraform", "plan", "-input=false", "-no-color"],
                              cwd=str(terraform_dir), capture_output=True, text=True, timeout=300)
        result.plan_ok = plan.returncode == 0
        result.passed = result.plan_ok
        if not result.plan_ok:
            result.errors.append((plan.stderr or plan.stdout or "terraform plan failed").strip()[:2000])
    except FileNotFoundError:
        result.skipped_reason = "terraform not in PATH; L2 skipped"
    except subprocess.TimeoutExpired:
        result.passed = False
        result.errors.append("terraform plan timed out")
    return result


def write_score_report(result, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    return path
