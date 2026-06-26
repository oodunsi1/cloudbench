from __future__ import annotations

from cloudbench.leaderboard import (
    aggregate_cases,
    build_leaderboard,
    failure_records,
    make_submission,
)

_CASES = [
    {"case_id": "aws-ec2-wordcount", "primary_service": "ec2", "building_block": "B0",
     "passed": True, "graph_match_score": 1.0, "repair_iterations": 0},
    {"case_id": "aws-ec2-java-image", "primary_service": "ec2", "building_block": "B1",
     "passed": True, "graph_match_score": 1.0, "repair_iterations": 1},
    {"case_id": "aws-s3-batch", "primary_service": "s3", "building_block": "B2",
     "passed": False, "graph_match_score": 0.8, "repair_iterations": 2,
     "graph_match": {"score": 0.8, "missing": ["s3"], "matched": ["compute"]}},
]


def test_aggregate_cases() -> None:
    agg = aggregate_cases(_CASES)
    assert agg["n_cases"] == 3
    assert agg["pass_rate_L1"] == round(2 / 3, 4)
    assert agg["graph_match_mean"] == round((1.0 + 1.0 + 0.8) / 3, 4)
    assert agg["repair_iterations_mean"] == round((0 + 1 + 2) / 3, 4)
    assert agg["by_primary_service"]["ec2"] == {"pass_rate_L1": 1.0, "n": 2}
    assert agg["by_primary_service"]["s3"] == {"pass_rate_L1": 0.0, "n": 1}


def test_make_submission_has_aggregate() -> None:
    sub = make_submission(submission_id="x", submitter="me", agent_or_model="gpt-x", cases=_CASES)
    assert sub["aggregate"]["pass_rate_L1"] == round(2 / 3, 4)
    assert sub["cloudbench_harness_version"]
    assert len(sub["cases"]) == 3


def test_build_leaderboard_ranks_by_pass_rate() -> None:
    strong = make_submission(submission_id="a", submitter="A", agent_or_model="strong",
                             cases=[c | {"passed": True} for c in _CASES])
    weak = make_submission(submission_id="b", submitter="B", agent_or_model="weak", cases=_CASES)
    board = build_leaderboard([weak, strong])
    assert board["rows"][0]["agent_or_model"] == "strong"  # 100% beats 67%
    assert "CloudBench leaderboard" in board["markdown"]
    assert "strong" in board["markdown"] and "weak" in board["markdown"]


def test_failure_records_only_failed() -> None:
    recs = failure_records(_CASES, agent_or_model="strong")
    assert len(recs) == 1
    r = recs[0]
    assert r["case_id"] == "aws-s3-batch"
    assert r["passed"] is False
    assert r["failure_mode"] == "graph_missing_family"
    assert "s3" in r["failure_detail"]
