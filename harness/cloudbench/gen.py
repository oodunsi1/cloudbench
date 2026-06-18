"""CloudBench generator — fill one spot on the map.

`bench generate --cell <id>` looks the cell up in ``benchmark/grid/cells.yaml``, copies the matching
recipe's template files into a fresh app repo under ``gen_out/<id>/``, builds the case file from the
recipe, validates that case, and writes a small run record (so the benchmark's own usage becomes
data). It never overwrites an already-pinned case unless forced — and even then it keeps the pin.
"""
from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from cloudbench.validate_ext import validate_cloudbench_case

_SHA_LEN = 40
_GITHUB_OWNER = "oodunsi1"


# --------------------------------------------------------------------------------------------------
# Locating the benchmark root + reading the map / recipes
# --------------------------------------------------------------------------------------------------

def find_root(start: Optional[Path] = None) -> Path:
    """Walk up from ``start`` (or cwd) to the folder that contains ``benchmark/grid/cells.yaml``."""
    here = (start or Path.cwd()).resolve()
    for cand in [here, *here.parents]:
        if (cand / "benchmark" / "grid" / "cells.yaml").is_file():
            return cand
    raise FileNotFoundError(
        "Could not find benchmark/grid/cells.yaml above "
        f"{here}. Run from the cloudbench folder or pass --root."
    )


def load_grid(root: Path) -> dict:
    return yaml.safe_load((root / "benchmark" / "grid" / "cells.yaml").read_text(encoding="utf-8"))


def find_cell(grid: dict, cell_id: str) -> dict:
    for cell in grid.get("cells", []):
        if cell.get("id") == cell_id:
            return cell
    known = ", ".join(c.get("id", "?") for c in grid.get("cells", []))
    raise KeyError(f"No cell '{cell_id}' in the map. Known cells: {known}")


def load_recipe(root: Path, cell: dict) -> dict:
    """Find the recipe for a cell — its explicit ``recipe:`` path, else recipes/<id>.yaml."""
    rel = cell.get("recipe") or f"benchmark/repos/recipes/{cell['id']}.yaml"
    path = root / rel
    if not path.is_file():
        raise FileNotFoundError(
            f"No recipe for cell '{cell['id']}' at {rel}. Author one (recipe-first) before generating."
        )
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------------------
# Turning a recipe into a case + an app repo
# --------------------------------------------------------------------------------------------------

def build_case(recipe: dict) -> dict:
    """Build a CloudBench case dict from a recipe (commit left unpinned — pinned after publish)."""
    sc = recipe.get("success_check", {})
    tc = recipe.get("teardown_check", {})
    case: Dict[str, Any] = {
        "id": recipe["cell"],
        "paper_id": recipe["cell"],
        "name": recipe["display_name"],
        "description": (recipe.get("description") or recipe["display_name"]).strip(),
        "repo_url": f"https://github.com/{_GITHUB_OWNER}/{recipe['repo_name']}",
        "commit": "unpinned",
        "level": recipe["level"],
        "provider": recipe["provider"],
        "primary_service": recipe.get("primary_service"),
        "aws_services": recipe.get("aws_services", []),
        "building_block": recipe["building_block"],
        "workload_kind": recipe["work_kind"],
        "ask_type": recipe.get("ask_type", "app-repo"),
        "runtime": recipe.get("runtime", {}),
        "expected_service_families": list(recipe["needs_service_families"]),
        "validation_contract": {
            "expected_status": "success",
            "run_instructions_summary": sc.get("run_instructions", "").strip(),
            "stdout_contains": sc.get("stdout_contains", []),
            "probe": sc.get("probe", {}),
        },
        "teardown_contract": {
            "method": tc.get("method", "terraform destroy"),
            "residual_check": tc.get("residual_check", ""),
            "proof_artifact": "terraform_runs/<slug>/<timestamp>/deployment_proof.json",
        },
    }
    return {k: v for k, v in case.items() if v is not None}


def materialize_app(root: Path, recipe: dict, dest: Path) -> List[str]:
    """Copy the recipe's template files into ``dest``. Returns the file names written."""
    template_dir = root / "benchmark" / "repos" / "templates" / recipe["archetype"]
    if not template_dir.is_dir():
        raise FileNotFoundError(f"No template folder for archetype '{recipe['archetype']}' at {template_dir}")
    dest.mkdir(parents=True, exist_ok=True)
    written: List[str] = []
    for name in recipe["app_files"]:
        src = template_dir / name
        if not src.is_file():
            raise FileNotFoundError(f"Template file missing: {src}")
        out = dest / name
        out.parent.mkdir(parents=True, exist_ok=True)  # support nested files (e.g. db/init.sql)
        out.write_bytes(src.read_bytes())
        if name == "run.sh":
            out.chmod(0o755)
        written.append(name)
    return written


def _preserve_pin(case: dict, existing_path: Path) -> None:
    """If a case file already exists with a pinned 40-hex commit, keep that pin (never lose it)."""
    if not existing_path.is_file():
        return
    try:
        old = yaml.safe_load(existing_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return
    commit = str(old.get("commit", ""))
    if len(commit) == _SHA_LEN and all(c in "0123456789abcdef" for c in commit.lower()):
        case["commit"] = commit


# --------------------------------------------------------------------------------------------------
# The run record (telemetry) — reuses CloudBot's outcome shape when available
# --------------------------------------------------------------------------------------------------

def _write_record(records_dir: Path, cell_id: str, passed: bool, errors: List[str]) -> Path:
    """Write a bench-shaped run record (case_id, tier, passed, stage, failure_mode, ...)."""
    run_id = f"gen-{cell_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    record: Dict[str, Any] = {
        "case_id": cell_id,
        "tier": "generate",
        "passed": passed,
        "stage": "complete" if passed else "generate",
        "failure_mode": None if passed else "generation_failed",
        "failure_detail": None if passed else "; ".join(errors)[:2000],
        "artifacts": {"run_id": run_id},
    }
    try:  # enrich with CloudBot's RunOutcome shape if paper2 is importable
        from cloudbot_common.outcome import RunOutcome, to_bench_record

        outcome = RunOutcome(
            run_id=run_id,
            repo_slug=cell_id,
            status="succeeded" if passed else "failed",
            failure_mode=None if passed else "generation_failed",
            failure_detail=None if passed else "; ".join(errors)[:2000],
        )
        record = to_bench_record(outcome, case_id=cell_id, tier="generate")
    except ImportError:
        pass

    records_dir.mkdir(parents=True, exist_ok=True)
    path = records_dir / f"{run_id}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return path


# --------------------------------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------------------------------

@dataclass
class GenerateResult:
    cell: str
    app_dir: str
    files_written: List[str] = field(default_factory=list)
    case_path: Optional[str] = None
    case_valid: bool = False
    case_written: bool = False
    record_path: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cell": self.cell,
            "app_dir": self.app_dir,
            "files_written": self.files_written,
            "case_path": self.case_path,
            "case_valid": self.case_valid,
            "case_written": self.case_written,
            "record_path": self.record_path,
            "errors": self.errors,
        }


def generate(
    root: Path,
    cell_id: str,
    *,
    out_root: Optional[Path] = None,
    records_dir: Optional[Path] = None,
    write_case: bool = True,
    force: bool = False,
) -> GenerateResult:
    """Fill one cell: materialise its app repo + case file, validate, and record the run."""
    out_root = out_root or (root / "gen_out")
    records_dir = records_dir or (out_root / "_records")

    grid = load_grid(root)
    cell = find_cell(grid, cell_id)
    recipe = load_recipe(root, cell)

    app_dir = out_root / cell_id
    result = GenerateResult(cell=cell_id, app_dir=str(app_dir))

    # 1) app repo
    result.files_written = materialize_app(root, recipe, app_dir)

    # 2) case file (never lose an existing pin)
    case = build_case(recipe)
    case_path = root / "benchmark" / "cases" / f"{cell_id}.yaml"
    _preserve_pin(case, case_path)

    # 3) self-check
    try:
        validate_cloudbench_case(case, require_pinned=False)
        result.case_valid = True
    except Exception as e:  # BenchmarkCaseError or anything malformed
        result.case_valid = False
        result.errors.append(str(e))

    # 4) write the case (only if valid; protect a published cell unless --force)
    if write_case and result.case_valid:
        if case_path.exists() and not force:
            result.case_path = str(case_path)
            result.errors.append(f"case exists; not overwriting without --force: {case_path}")
        else:
            case_path.write_text(
                yaml.safe_dump(
                    case, sort_keys=False, default_flow_style=False, allow_unicode=True, width=100
                ),
                encoding="utf-8",
            )
            result.case_path = str(case_path)
            result.case_written = True
    elif result.case_valid:
        result.case_path = str(case_path)

    # 5) run record (telemetry)
    passed = result.case_valid and not [e for e in result.errors if "case exists" not in e]
    result.record_path = str(_write_record(records_dir, cell_id, passed, result.errors))
    return result
