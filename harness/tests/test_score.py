from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT.parent / "benchmark" / "cases"
PAPER2_COMMON = Path(__file__).resolve().parents[3] / "cloudbot-paper2" / "cloudbot-common"

if PAPER2_COMMON.is_dir():
    sys.path.insert(0, str(PAPER2_COMMON))


@pytest.fixture
def uc1_case() -> dict:
    return yaml.safe_load((CASES / "uc1.yaml").read_text(encoding="utf-8"))


@pytest.fixture
def sample_terraform_dir(tmp_path: Path) -> Path:
    (tmp_path / "main.tf").write_text(
        """
resource "aws_instance" "app" {}
resource "aws_security_group" "app" {}
resource "aws_iam_role" "app" {}
resource "aws_iam_instance_profile" "app" {}
""",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def sample_archspec() -> dict:
    return {
        "components": [
            {"id": "compute", "service_family": "compute"},
            {"id": "sg", "service_family": "security_group"},
        ],
        "stateful_deps": [],
    }


def test_validate_uc_cases(uc1_case: dict) -> None:
    from cloudbench.validate_ext import validate_cloudbench_case

    for name in ("uc1.yaml", "uc2.yaml", "uc3.yaml"):
        case = yaml.safe_load((CASES / name).read_text(encoding="utf-8"))
        validate_cloudbench_case(case)


def test_graph_match_full(sample_terraform_dir: Path, uc1_case: dict) -> None:
    from cloudbench.graph import families_from_terraform, graph_match_score

    observed = families_from_terraform(sample_terraform_dir)
    result = graph_match_score(uc1_case["expected_service_families"], observed)
    assert result["score"] == 1.0
    assert result["missing"] == []


def test_score_l1_passes(tmp_path: Path, uc1_case: dict, sample_terraform_dir: Path, sample_archspec: dict) -> None:
    from cloudbench.score import score_l1

    arch = tmp_path / "archspec.json"
    arch.write_text(json.dumps(sample_archspec), encoding="utf-8")
    result = score_l1(
        uc1_case,
        archspec_path=arch,
        terraform_dir=sample_terraform_dir,
        skip_terraform_validate=True,
    )
    assert result.graph_match["score"] == 1.0
    assert result.passed is True


def test_score_l1_missing_family(tmp_path: Path, uc1_case: dict) -> None:
    from cloudbench.score import score_l1

    incomplete = tmp_path / "main.tf"
    incomplete.write_text('resource "aws_instance" "app" {}\n', encoding="utf-8")
    result = score_l1(
        uc1_case,
        terraform_dir=tmp_path,
        skip_terraform_validate=True,
    )
    assert result.graph_match["score"] < 1.0
    assert result.passed is False


def test_require_pinned_rejects_unpinned(uc1_case: dict) -> None:
    from cloudbot_common.benchmark import BenchmarkCaseError
    from cloudbench.validate_ext import validate_cloudbench_case

    bad = dict(uc1_case)
    bad["commit"] = "unpinned"
    with pytest.raises(BenchmarkCaseError):
        validate_cloudbench_case(bad, require_pinned=True)
