#!/usr/bin/env python3
"""Keep the human docs in sync with the single source of truth (benchmark/grid/cells.yaml).

Renders the canonical case table from cells.yaml and splices it between
``<!-- cases:start -->`` / ``<!-- cases:end -->`` markers in the docs that list cases (README.md and
benchmark/BUILDING_BLOCKS.md). Idempotent. Run it after adding or changing a case. The drift test
``harness/tests/test_docs_in_sync.py`` fails if the docs fall behind, so this can't be silently
forgotten — the docs are GENERATED, never hand-maintained.

Usage:
  python scripts/sync_docs.py          # write the tables (default)
  python scripts/sync_docs.py --check  # exit non-zero if any doc is out of sync (for CI/tests)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[1]
_CELLS = _ROOT / "benchmark" / "grid" / "cells.yaml"
_TARGETS = [_ROOT / "README.md", _ROOT / "benchmark" / "BUILDING_BLOCKS.md"]
_START, _END = "<!-- cases:start -->", "<!-- cases:end -->"
_ICON = {"covered": "✅", "planned": "🛠", "empty": "▫"}
_PROVIDER_ORDER = {"aws": 0, "gcp": 1, "azure": 2, "alibaba": 3}


def load_cells() -> list:
    return yaml.safe_load(_CELLS.read_text(encoding="utf-8")).get("cells", [])


def render_table(cells: list) -> str:
    rows = sorted(cells, key=lambda c: (_PROVIDER_ORDER.get(c.get("provider"), 9),
                                        c.get("building_block", ""), c.get("id", "")))
    lines = ["| Case | Block | Workload | Cloud | Status | App repo |",
             "|------|-------|----------|-------|--------|----------|"]
    for c in rows:
        repo = (c.get("repo") or "").rstrip("/")
        link = f"[{repo.split('/')[-1]}]({repo})" if repo else "—"
        icon = _ICON.get(c.get("status"), "")
        lines.append(f"| `{c.get('id','')}` | {c.get('building_block','')} | {c.get('work_kind','')} "
                     f"| {c.get('provider','')} | {icon} {c.get('status','')} | {link} |")
    covered = sum(1 for c in rows if c.get("status") == "covered")
    providers = sorted({c.get("provider") for c in rows}, key=lambda p: _PROVIDER_ORDER.get(p, 9))
    lines += ["", f"_{covered} covered of {len(rows)} cases across {len(providers)} clouds "
                  f"({', '.join(providers)}). Generated from `benchmark/grid/cells.yaml` by "
                  f"`scripts/sync_docs.py` — do not edit between the markers._"]
    return "\n".join(lines)


def splice(path: Path, table: str, check: bool) -> bool:
    """Return True if the file is (or would be) changed. Raises if markers are missing."""
    text = path.read_text(encoding="utf-8")
    if _START not in text or _END not in text:
        raise SystemExit(f"{path.name}: missing markers {_START} / {_END} — add them once, then re-run.")
    pre, rest = text.split(_START, 1)
    _, post = rest.split(_END, 1)
    new = f"{pre}{_START}\n{table}\n{_END}{post}"
    if new != text and not check:
        path.write_text(new, encoding="utf-8")
    return new != text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit non-zero if out of sync; don't write")
    args = ap.parse_args()
    table = render_table(load_cells())
    drifted = [t.name for t in _TARGETS if splice(t, table, args.check)]
    if args.check and drifted:
        print("docs OUT OF SYNC with cells.yaml (run: python scripts/sync_docs.py): "
              + ", ".join(drifted), file=sys.stderr)
        return 1
    print(f"sync_docs: {'in sync' if not drifted else 'updated ' + ', '.join(drifted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
