"""Guard against the recurring 'source changed but the page didn't' bug: the case docs (README +
BUILDING_BLOCKS) must stay in sync with benchmark/grid/cells.yaml (the single source of truth). If a
case is added/changed in cells.yaml but scripts/sync_docs.py wasn't re-run, this FAILS — so the docs
can never silently fall behind."""
import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


def _load_sync():
    spec = importlib.util.spec_from_file_location("sync_docs", _ROOT / "scripts" / "sync_docs.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_case_docs_match_cells_yaml():
    m = _load_sync()
    table = m.render_table(m.load_cells())
    stale = [t.name for t in m._TARGETS if m.splice(t, table, check=True)]
    assert not stale, f"out of sync with cells.yaml — run `python scripts/sync_docs.py`: {stale}"


def test_every_covered_case_is_in_the_readme():
    m = _load_sync()
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    missing = [c["id"] for c in m.load_cells()
               if c.get("status") == "covered" and c["id"] not in readme]
    assert not missing, f"covered cases missing from README: {missing}"
