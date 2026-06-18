from __future__ import annotations

import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]          # harness/
BENCH_ROOT = HARNESS.parent                            # cloudbench/
PAPER2_COMMON = Path(__file__).resolve().parents[3] / "cloudbot-paper2" / "cloudbot-common"

if PAPER2_COMMON.is_dir():
    sys.path.insert(0, str(PAPER2_COMMON))


def test_aws_services_includes_core() -> None:
    from cloudbench.catalog import aws_services

    ids = {s["id"] for s in aws_services()}
    assert {"ec2", "s3", "rds", "lambda"}.issubset(ids)
    assert len(ids) > 100  # the SDK knows hundreds of services


def test_build_catalog_categorises_and_cross_links() -> None:
    from cloudbench.catalog import build_catalog

    cat = build_catalog(BENCH_ROOT, "aws")
    by_id = {s["id"]: s for s in cat["services"]}
    assert by_id["ec2"]["category"] == "compute"
    assert by_id["s3"]["category"] == "storage"
    assert by_id["rds"]["category"] == "database"
    assert by_id["s3"]["target_repo"] == "cloudbench-aws-s3"  # follows NAMING.md
    # the services we've built cross-link to a cell
    assert by_id["s3"]["status"] in ("covered", "generated")
    assert by_id["s3"]["cell"]
    assert cat["counts"]["total"] == len(cat["services"])


def test_diff_detects_added_and_removed() -> None:
    from cloudbench.catalog import diff_catalogs

    old = {"services": [{"id": "ec2"}, {"id": "s3"}]}
    new = {"services": [{"id": "ec2"}, {"id": "lambda"}]}
    d = diff_catalogs(old, new)
    assert d["added"] == ["lambda"]
    assert d["removed"] == ["s3"]


def test_catalog_build_is_stable() -> None:
    """Two clean builds must be identical (the watcher should report no spurious changes)."""
    from cloudbench.catalog import build_catalog, diff_catalogs

    a = build_catalog(BENCH_ROOT, "aws")
    b = build_catalog(BENCH_ROOT, "aws")
    assert diff_catalogs(a, b) == {"added": [], "removed": []}
