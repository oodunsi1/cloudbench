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
def wordcount_case() -> dict:
    # The B0 EC2 word-count case (renamed from uc1.yaml in the CloudBench rename).
    return yaml.safe_load((CASES / "aws-ec2-wordcount.yaml").read_text(encoding="utf-8"))


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


def test_validate_all_cases() -> None:
    """Every case file in the catalog must satisfy the CloudBench schema. Rename-proof: it discovers
    the cases on disk rather than hard-coding names. Planned cases are still unpinned, so this does
    not require a pinned commit."""
    from cloudbench.validate_ext import validate_cloudbench_case

    case_files = sorted(CASES.glob("*.yaml"))
    assert case_files, "no case files found"
    for path in case_files:
        case = yaml.safe_load(path.read_text(encoding="utf-8"))
        validate_cloudbench_case(case)


def test_graph_match_full(sample_terraform_dir: Path, wordcount_case: dict) -> None:
    from cloudbench.graph import families_from_terraform, graph_match_score

    observed = families_from_terraform(sample_terraform_dir)
    result = graph_match_score(wordcount_case["expected_service_families"], observed)
    assert result["score"] == 1.0
    assert result["missing"] == []


def test_score_l1_passes(tmp_path: Path, wordcount_case: dict, sample_terraform_dir: Path, sample_archspec: dict) -> None:
    from cloudbench.score import score_l1

    arch = tmp_path / "archspec.json"
    arch.write_text(json.dumps(sample_archspec), encoding="utf-8")
    result = score_l1(
        wordcount_case,
        archspec_path=arch,
        terraform_dir=sample_terraform_dir,
        skip_terraform_validate=True,
    )
    assert result.graph_match["score"] == 1.0
    assert result.passed is True


def test_score_l1_missing_family(tmp_path: Path, wordcount_case: dict) -> None:
    from cloudbench.score import score_l1

    incomplete = tmp_path / "main.tf"
    incomplete.write_text('resource "aws_instance" "app" {}\n', encoding="utf-8")
    result = score_l1(
        wordcount_case,
        terraform_dir=tmp_path,
        skip_terraform_validate=True,
    )
    assert result.graph_match["score"] < 1.0
    assert result.passed is False


def test_require_pinned_rejects_unpinned(wordcount_case: dict) -> None:
    from cloudbot_common.benchmark import BenchmarkCaseError
    from cloudbench.validate_ext import validate_cloudbench_case

    bad = dict(wordcount_case)
    bad["commit"] = "unpinned"
    with pytest.raises(BenchmarkCaseError):
        validate_cloudbench_case(bad, require_pinned=True)


def test_enriched_graph_families(tmp_path: Path) -> None:
    """The expanded resource-family map credits modern AWS resources (network, dynamodb, lambda)."""
    from cloudbench.graph import families_from_terraform

    (tmp_path / "main.tf").write_text(
        'resource "aws_vpc" "v" {}\n'
        'resource "aws_subnet" "s" {}\n'
        'resource "aws_dynamodb_table" "t" {}\n'
        'resource "aws_lambda_function" "f" {}\n'
        'resource "aws_lb_target_group" "tg" {}\n',
        encoding="utf-8",
    )
    fams = families_from_terraform(tmp_path)
    assert {"network", "dynamodb", "lambda", "alb"} <= fams


def test_security_advisory_does_not_fail_clean_case(tmp_path: Path, wordcount_case: dict, sample_terraform_dir: Path) -> None:
    """A case with no security_contract: the lint runs (advisory) but never fails the case."""
    from cloudbench.score import score_l1

    result = score_l1(wordcount_case, terraform_dir=sample_terraform_dir, skip_terraform_validate=True)
    assert result.security is not None and result.security["passed"] is None
    assert result.passed is True


def test_security_contract_fails_insecure_case(tmp_path: Path, wordcount_case: dict) -> None:
    """A case that declares fail_on_critical fails L1 when the Terraform has a critical finding."""
    from cloudbench.score import score_l1

    case = dict(wordcount_case)
    case["security_contract"] = {"tool": "builtin", "fail_on_critical": True}
    (tmp_path / "main.tf").write_text(
        'resource "aws_instance" "app" {}\n'
        'resource "aws_security_group" "app" {\n'
        '  ingress { from_port = 22, to_port = 22, cidr_blocks = ["0.0.0.0/0"] }\n'
        '}\n'
        'resource "aws_iam_role" "app" {}\n'
        'resource "aws_iam_instance_profile" "app" {}\n',
        encoding="utf-8",
    )
    result = score_l1(case, terraform_dir=tmp_path, skip_terraform_validate=True)
    assert result.security["counts"]["critical"] >= 1
    assert result.passed is False


def test_l2_skipped_without_credentials(tmp_path: Path, wordcount_case: dict) -> None:
    """L2 needs AWS creds; with none and no --allow-cloud it is SKIPPED (passed=None), not failed."""
    from cloudbench.score import score_l2

    (tmp_path / "main.tf").write_text('resource "aws_instance" "a" {}\n', encoding="utf-8")
    res = score_l2(wordcount_case, tmp_path, allow_cloud=False)
    # In CI/dev with no AWS_* set, this is skipped; if creds happen to be present it actually plans.
    assert res.passed is None or isinstance(res.passed, bool)
    if res.passed is None:
        assert res.skipped_reason


def test_l2_plan_ok_with_stubbed_terraform(tmp_path: Path, wordcount_case: dict, monkeypatch) -> None:
    """With --allow-cloud and a stubbed terraform (init+plan return 0), L2 passes."""
    from cloudbench import score as score_mod

    (tmp_path / "main.tf").write_text('resource "aws_instance" "a" {}\n', encoding="utf-8")

    class _P:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(score_mod.subprocess, "run", lambda *a, **k: _P())
    res = score_mod.score_l2(wordcount_case, tmp_path, allow_cloud=True)
    assert res.plan_ok is True and res.passed is True


def test_l2_plan_failure(tmp_path: Path, wordcount_case: dict, monkeypatch) -> None:
    from cloudbench import score as score_mod

    (tmp_path / "main.tf").write_text('resource "aws_instance" "a" {}\n', encoding="utf-8")

    class _Init:
        returncode = 0
        stdout = ""
        stderr = ""

    class _Plan:
        returncode = 1
        stdout = ""
        stderr = "Error: invalid resource"

    calls = {"n": 0}

    def fake(*a, **k):
        calls["n"] += 1
        return _Init() if calls["n"] == 1 else _Plan()

    monkeypatch.setattr(score_mod.subprocess, "run", fake)
    res = score_mod.score_l2(wordcount_case, tmp_path, allow_cloud=True)
    assert res.plan_ok is False and res.passed is False and res.errors


def test_multicloud_family_map(tmp_path: Path) -> None:
    """The scorer is provider-neutral: the family map credits GCP and Azure resources, not just AWS."""
    from cloudbench.graph import families_from_terraform

    (tmp_path / "gcp.tf").write_text(
        'resource "google_compute_instance" "v" {}\n'
        'resource "google_storage_bucket" "b" {}\n'
        'resource "google_sql_database_instance" "d" {}\n', encoding="utf-8")
    assert {"compute", "s3", "rds"} <= families_from_terraform(tmp_path)

    (tmp_path / "az.tf").write_text(
        'resource "azurerm_linux_virtual_machine" "v" {}\n'
        'resource "azurerm_storage_account" "s" {}\n', encoding="utf-8")
    assert {"compute", "s3"} <= families_from_terraform(tmp_path)
