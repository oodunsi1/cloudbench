from __future__ import annotations

import re
from typing import Any, Dict, List

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

CLOUDBENCH_OPTIONAL_FIELDS = {
    "paper_id", "level", "building_block", "runtime", "description",
    "baseline_eligible", "security_contract", "cost_ceiling_usd", "ask_type",
}


def collect_cloudbench_errors(case: dict, *, require_pinned: bool = False) -> List[str]:
    """Extended validation beyond cloudbot_common.benchmark."""
    errors: List[str] = []
    if "level" not in case:
        errors.append("'level' is required for CloudBench cases")
    elif not isinstance(case.get("level"), int):
        errors.append("'level' must be an integer")
    commit = case.get("commit")
    if require_pinned:
        if not isinstance(commit, str) or commit == "unpinned":
            errors.append("'commit' must be a pinned 40-char SHA for release scoring")
        elif not _SHA_RE.match(commit.lower()):
            errors.append("'commit' must be a 40-char hex SHA for release scoring")
    if "security_contract" in case and not isinstance(case["security_contract"], dict):
        errors.append("'security_contract' must be a mapping/object")
    if "baseline_eligible" in case:
        be = case["baseline_eligible"]
        if not isinstance(be, list) or not all(isinstance(x, str) for x in be):
            errors.append("'baseline_eligible' must be a string array")
    return errors


def validate_cloudbench_case(case: dict, *, require_pinned: bool = False) -> dict:
    from cloudbot_common.benchmark import BenchmarkCaseError, validate_benchmark_case

    validate_benchmark_case(case)
    extra = collect_cloudbench_errors(case, require_pinned=require_pinned)
    if extra:
        raise BenchmarkCaseError(extra)
    return case
