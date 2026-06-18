from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest
import yaml

HARNESS = Path(__file__).resolve().parents[1]          # harness/
BENCH_ROOT = HARNESS.parent                             # cloudbench/
PAPER2_COMMON = Path(__file__).resolve().parents[3] / "cloudbot-paper2" / "cloudbot-common"

if PAPER2_COMMON.is_dir():
    sys.path.insert(0, str(PAPER2_COMMON))


def _golden_recipe() -> dict:
    return yaml.safe_load(
        (BENCH_ROOT / "benchmark" / "repos" / "recipes" / "aws-s3-batch.yaml").read_text(encoding="utf-8")
    )


def test_build_case_from_golden_recipe_is_valid() -> None:
    from cloudbench.gen import build_case
    from cloudbench.validate_ext import validate_cloudbench_case

    case = build_case(_golden_recipe())
    validate_cloudbench_case(case)  # must not raise
    assert case["id"] == "aws-s3-batch"
    assert {"compute", "s3"}.issubset(set(case["expected_service_families"]))
    assert case["commit"] == "unpinned"  # generated cases start unpinned


def test_generate_materializes_app_and_validates(tmp_path: Path) -> None:
    from cloudbench.gen import generate

    res = generate(
        BENCH_ROOT, "aws-s3-batch",
        out_root=tmp_path, records_dir=tmp_path / "_rec", write_case=False,
    )
    assert res.case_valid is True
    assert "process.py" in res.files_written
    app = tmp_path / "aws-s3-batch"
    assert (app / "process.py").is_file()
    assert (app / "run.sh").stat().st_mode & 0o111  # run.sh is executable

    record = json.loads(Path(res.record_path).read_text(encoding="utf-8"))
    assert record["case_id"] == "aws-s3-batch"
    assert record["passed"] is True


def test_generated_app_actually_runs(tmp_path: Path) -> None:
    """The materialised app — not just the original — must run against a fake S3."""
    from cloudbench.gen import generate

    generate(BENCH_ROOT, "aws-s3-batch", out_root=tmp_path, records_dir=tmp_path / "_rec", write_case=False)
    spec = importlib.util.spec_from_file_location("gen_s3_process", tmp_path / "aws-s3-batch" / "process.py")
    proc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proc)

    class FakeS3:
        def __init__(self) -> None:
            self.store: dict[tuple[str, str], bytes] = {}

        def get_object(self, Bucket, Key):  # noqa: N803
            return {"Body": io.BytesIO(self.store[(Bucket, Key)])}

        def put_object(self, Bucket, Key, Body, **kwargs):  # noqa: N803
            self.store[(Bucket, Key)] = Body

    s3 = FakeS3()
    s3.store[("b", "input.txt")] = b"a a b"
    uri = proc.process(s3, "b", "input.txt", "out.json")
    assert uri == "s3://b/out.json"
    assert json.loads(s3.store[("b", "out.json")])["word_counts"]["a"] == 2


def test_generate_second_archetype_with_nested_files(tmp_path: Path) -> None:
    """The engine must handle a different shape (web service + DB) and nested files (db/init.sql)."""
    from cloudbench.gen import generate

    res = generate(
        BENCH_ROOT, "aws-rds-api",
        out_root=tmp_path, records_dir=tmp_path / "_rec", write_case=False,
    )
    assert res.case_valid is True
    assert "app.py" in res.files_written
    assert "db/init.sql" in res.files_written
    assert (tmp_path / "aws-rds-api" / "db" / "init.sql").is_file()


def test_preserve_pin_keeps_existing_sha(tmp_path: Path) -> None:
    from cloudbench.gen import _preserve_pin

    sha = "a" * 40
    case_file = tmp_path / "case.yaml"
    case_file.write_text(f"commit: {sha}\n", encoding="utf-8")
    case = {"commit": "unpinned"}
    _preserve_pin(case, case_file)
    assert case["commit"] == sha


def test_unknown_cell_raises() -> None:
    from cloudbench.gen import find_cell, load_grid

    grid = load_grid(BENCH_ROOT)
    with pytest.raises(KeyError):
        find_cell(grid, "does-not-exist")
