"""Leaderboard + failure-registry tooling — turn per-case scores into the published artifacts.

Three jobs, all pure-data (no cloud):
  * make_submission  — fold a system's per-case results into one submission record + its aggregate
                       (the shape LEADERBOARD.md specifies).
  * build_leaderboard — ingest every submission JSON and rank them into a markdown table.
  * failure_records  — emit FAILURE_REGISTRY records for the failed cases (the public improvement loop).

Dependency-free. The CLI exposes `bench leaderboard build` and `bench leaderboard submission`.
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

HARNESS_VERSION = "0.1.0"


def _num(values: List[Any]) -> List[float]:
    return [float(v) for v in values if isinstance(v, (int, float))]


def aggregate_cases(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The reporting aggregate over a system's per-case rows (LEADERBOARD.md columns)."""
    n = len(cases)
    passed = [c for c in cases if c.get("passed")]
    gm = _num([c.get("graph_match_score") for c in cases])
    reps = _num([c.get("repair_iterations") for c in cases])
    costs = _num([c.get("cost_usd") for c in cases])

    by_service: Dict[str, Dict[str, Any]] = {}
    for c in cases:
        svc = c.get("primary_service") or "unknown"
        b = by_service.setdefault(svc, {"n": 0, "passed": 0})
        b["n"] += 1
        b["passed"] += 1 if c.get("passed") else 0
    for svc, b in by_service.items():
        b["pass_rate_L1"] = round(b["passed"] / b["n"], 4) if b["n"] else None

    return {
        "pass_rate_L1": round(len(passed) / n, 4) if n else None,
        "pass_rate_L3": None,
        "pass_rate_L4": None,
        "graph_match_mean": round(mean(gm), 4) if gm else None,
        "repair_iterations_mean": round(mean(reps), 4) if reps else None,
        "cost_usd_mean": round(mean(costs), 6) if costs else None,
        "n_cases": n,
        "by_primary_service": {k: {"pass_rate_L1": v["pass_rate_L1"], "n": v["n"]} for k, v in by_service.items()},
    }


def make_submission(
    *,
    submission_id: str,
    submitter: str,
    agent_or_model: str,
    cases: List[Dict[str, Any]],
    agent_type: str = "unknown",
    tier_claimed: str = "L1",
    timestamp: str = "",
    harness_version: str = HARNESS_VERSION,
    **extra: Any,
) -> Dict[str, Any]:
    """Build one leaderboard submission record (per LEADERBOARD.md) with its aggregate filled in."""
    sub = {
        "submission_id": submission_id,
        "submitter": submitter,
        "agent_or_model": agent_or_model,
        "agent_type": agent_type,
        "cloudbench_harness_version": harness_version,
        "tier_claimed": tier_claimed,
        "timestamp": timestamp,
        "cases": cases,
        "aggregate": aggregate_cases(cases),
    }
    sub.update(extra)
    return sub


def load_submissions(submissions_dir: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for p in sorted(Path(submissions_dir).glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def _row(sub: Dict[str, Any]) -> Dict[str, Any]:
    agg = sub.get("aggregate") or {}
    return {
        "agent_or_model": sub.get("agent_or_model", "?"),
        "agent_type": sub.get("agent_type", "?"),
        "tier": sub.get("tier_claimed", "L1"),
        "n_cases": agg.get("n_cases"),
        "pass_rate_L1": agg.get("pass_rate_L1"),
        "graph_match_mean": agg.get("graph_match_mean"),
        "repair_iterations_mean": agg.get("repair_iterations_mean"),
        "cost_usd_mean": agg.get("cost_usd_mean"),
        "submission_id": sub.get("submission_id"),
    }


def _fmt(v: Any, pct: bool = False) -> str:
    if v is None:
        return "—"
    if pct and isinstance(v, (int, float)):
        return f"{v * 100:.0f}%"
    if isinstance(v, float):
        return f"{v:.3f}".rstrip("0").rstrip(".")
    return str(v)


def build_leaderboard(submissions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Rank submissions (by L1 pass-rate, then graph-match) and render a markdown table."""
    rows = sorted(
        (_row(s) for s in submissions),
        key=lambda r: (-(r["pass_rate_L1"] or 0), -(r["graph_match_mean"] or 0)),
    )
    header = "| Rank | System | Type | Cases | Pass@L1 | GraphMatch | Repairs | Cost/run |"
    sep = "|---|---|---|---|---|---|---|---|"
    lines = [
        "# CloudBench leaderboard",
        "",
        f"Built from {len(rows)} submission(s) by the harness. Ranked by L1 pass-rate, then graph match.",
        "",
        header,
        sep,
    ]
    for i, r in enumerate(rows, 1):
        lines.append(
            f"| {i} | {r['agent_or_model']} | {r['agent_type']} | {_fmt(r['n_cases'])} | "
            f"{_fmt(r['pass_rate_L1'], pct=True)} | {_fmt(r['graph_match_mean'])} | "
            f"{_fmt(r['repair_iterations_mean'])} | "
            f"{('$' + _fmt(r['cost_usd_mean'])) if r['cost_usd_mean'] is not None else '—'} |"
        )
    return {"rows": rows, "markdown": "\n".join(lines) + "\n"}


def failure_records(
    cases: List[Dict[str, Any]],
    *,
    agent_or_model: str,
    timestamp: str = "",
    harness_version: str = HARNESS_VERSION,
    registry_version: str = "1.0",
) -> List[Dict[str, Any]]:
    """FAILURE_REGISTRY records for the failed cases — the public improvement loop's data points."""
    records: List[Dict[str, Any]] = []
    for c in cases:
        if c.get("passed"):
            continue
        gm = c.get("graph_match") or {}
        records.append({
            "registry_version": registry_version,
            "case_id": c.get("case_id"),
            "paper_id": c.get("paper_id") or c.get("case_id"),
            "provider": c.get("provider", "aws"),
            "primary_service": c.get("primary_service"),
            "building_block": c.get("building_block"),
            "tier": c.get("tier", "L1"),
            "passed": False,
            "stage": c.get("stage", "engineer"),
            "failure_mode": c.get("failure_mode") or ("graph_missing_family" if gm.get("missing") else "other"),
            "failure_detail": c.get("failure_detail")
                or (f"expected {', '.join(gm.get('missing', []))}, observed none" if gm.get("missing") else ""),
            "graph_match": {k: gm.get(k) for k in ("score", "missing", "matched") if k in gm},
            "agent_or_model": agent_or_model,
            "harness_version": harness_version,
            "timestamp": timestamp,
        })
    return records
