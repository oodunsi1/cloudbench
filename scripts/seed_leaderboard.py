#!/usr/bin/env python3
"""Seed the leaderboard from the real artifact-tier baseline runs that already exist.

Reads the per-case baseline result JSONs produced by the paper repo (E5, MACOG, IaCGen on the three
EC2 cases) and turns each system into a proper CloudBench leaderboard submission, then builds the
LEADERBOARD table and exports a failure registry. This makes the (previously empty) leaderboard and
failure registry real, using measured data — no new runs.

L1 pass here is honest: the IaC must be terraform-valid AND match the full expected service graph.

CloudBot itself is added the same way once its generated IaC is scored with `bench score --tier L1`
(its clean numbers today are deploy-tier, which is a different, gated column).

Usage: python scripts/seed_leaderboard.py [--paper2 <path>] [--write]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "harness"))

from cloudbench.leaderboard import build_leaderboard, failure_records, make_submission  # noqa: E402

# Old case id -> (case id, primary_service, building_block) for the three published EC2 cases.
_UC = {
    "uc1": ("aws-ec2-wordcount", "ec2", "B0"),
    "uc2": ("aws-ec2-java-image", "ec2", "B1"),
    "uc3": ("aws-ec2-java-video", "ec2", "B1"),
}
_SYSTEMS = {
    "e5": ("E5 generic agent", "agent"),
    "macog": ("MACOG multi-agent", "multi_agent"),
    "iacgen": ("IaCGen", "single_model"),
}


def _case_row(data: dict, uc: str) -> dict:
    case_id, svc, block = _UC[uc]
    graph = data.get("graph") or {}
    score = graph.get("score")
    valid = data.get("terraform_valid")
    passed = bool(valid) and isinstance(score, (int, float)) and score >= 1.0
    return {
        "case_id": case_id,
        "primary_service": svc,
        "building_block": block,
        "tier": "L1",
        "passed": passed,
        "graph_match_score": score,
        "graph_match": {"score": score, "missing": graph.get("missing", []),
                        "matched": graph.get("found", [])},
        "repair_iterations": data.get("repair_attempts", 0),
        "terraform_valid": valid,
        "tokens_in": data.get("prompt_tokens"),
        "tokens_out": data.get("completion_tokens"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper2", default=str(Path.home() / "Documents/PhD/cloudbot-paper2"),
                    help="Path to the cloudbot-paper2 repo (source of the baseline result JSONs)")
    ap.add_argument("--write", action="store_true", help="Write submissions + LEADERBOARD.md (else dry-run)")
    args = ap.parse_args()

    data_dir = Path(args.paper2) / "docs" / "paper" / "data" / "baselines"
    if not data_dir.is_dir():
        print(f"baseline data dir not found: {data_dir}", file=sys.stderr)
        return 1

    sub_dir = _ROOT / "experiments" / "leaderboard" / "submissions"
    submissions = []
    failures = []
    for system, (name, atype) in _SYSTEMS.items():
        cases = []
        for uc in _UC:
            fp = data_dir / f"{system}_{uc}.json"
            if not fp.exists():
                continue
            cases.append(_case_row(json.loads(fp.read_text(encoding="utf-8")), uc))
        if not cases:
            continue
        sub = make_submission(
            submission_id=f"{system}-cloudbench-v1-artifact",
            submitter="CloudBench paper (measured)",
            agent_or_model=name,
            agent_type=atype,
            tier_claimed="L1",
            cases=cases,
        )
        submissions.append(sub)
        failures.extend(failure_records(cases, agent_or_model=name))
        if args.write:
            sub_dir.mkdir(parents=True, exist_ok=True)
            (sub_dir / f"{system}-artifact.json").write_text(json.dumps(sub, indent=2), encoding="utf-8")

    board = build_leaderboard(submissions)
    if args.write:
        (_ROOT / "experiments" / "leaderboard" / "LEADERBOARD.md").write_text(board["markdown"], encoding="utf-8")
        (_ROOT / "experiments" / "leaderboard" / "failure_registry.json").write_text(
            json.dumps(failures, indent=2), encoding="utf-8")
        print(f"Wrote {len(submissions)} submission(s), LEADERBOARD.md, and {len(failures)} failure record(s) "
              f"to {sub_dir.parent}", file=sys.stderr)
    print(board["markdown"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
