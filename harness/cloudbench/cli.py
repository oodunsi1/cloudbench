#!/usr/bin/env python3
"""CloudBench CLI — validate cases and score pipeline runs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from cloudbench.catalog import build_catalog, catalog_path, refresh, write_catalog
from cloudbench.gen import find_root, generate
from cloudbench.score import score_l1, write_score_report
from cloudbench.validate_ext import validate_cloudbench_case


def _load_case(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Case file must be a YAML mapping: {path}")
    return data


def cmd_validate(args: argparse.Namespace) -> int:
    case = _load_case(Path(args.case))
    validate_cloudbench_case(case, require_pinned=args.require_pinned)
    print(f"OK: {case['id']}", file=sys.stderr)
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    case = _load_case(Path(args.case))
    tier = args.tier.upper()
    if tier != "L1":
        print(f"Tier {tier} not implemented yet (L3/L4 require cloud approval).", file=sys.stderr)
        return 2
    result = score_l1(
        case,
        repospec_path=Path(args.repospec) if args.repospec else None,
        archspec_path=Path(args.archspec) if args.archspec else None,
        terraform_dir=Path(args.terraform_dir) if args.terraform_dir else None,
        skip_terraform_validate=args.skip_terraform_validate,
    )
    out = Path(args.output) if args.output else None
    if out:
        write_score_report(result, out)
        print(f"Wrote {out}", file=sys.stderr)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.passed else 1


def cmd_generate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve() if args.root else find_root()
    result = generate(
        root,
        args.cell,
        out_root=Path(args.out) if args.out else None,
        records_dir=Path(args.records_dir) if args.records_dir else None,
        write_case=not args.no_case,
        force=args.force,
    )
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.case_valid else 1


def cmd_catalog(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve() if args.root else find_root()
    if args.refresh:
        catalog, diff, path = refresh(root, args.provider)
        print(f"Refreshed {path}", file=sys.stderr)
        print(json.dumps(
            {"counts": catalog["counts"], "added": diff["added"], "removed": diff["removed"]},
            indent=2,
        ))
        return 0
    catalog = build_catalog(root, args.provider)
    if not args.dry_run:
        path = write_catalog(catalog, catalog_path(root, args.provider))
        print(f"Wrote {path}", file=sys.stderr)
    print(json.dumps({"counts": catalog["counts"], "categories": len(catalog["category_groups"])}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="bench", description="CloudBench harness")
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="Validate a case YAML")
    v.add_argument("case", help="Path to case YAML")
    v.add_argument("--require-pinned", action="store_true", help="Reject unpinned commits")
    v.set_defaults(func=cmd_validate)

    s = sub.add_parser("score", help="Score a pipeline run")
    s.add_argument("case", help="Path to case YAML")
    s.add_argument("--tier", default="L1", choices=["L1", "L2", "L3", "L4"])
    s.add_argument("--repospec", help="Path to repospec.json from a run")
    s.add_argument("--archspec", help="Path to archspec.json from a run")
    s.add_argument("--terraform-dir", help="Path to terraform run directory")
    s.add_argument("--output", "-o", help="Write JSON score report to path")
    s.add_argument("--skip-terraform-validate", action="store_true")
    s.set_defaults(func=cmd_score)

    g = sub.add_parser("generate", help="Fill one map cell: scaffold app repo + case from its recipe")
    g.add_argument("--cell", required=True, help="Cell id from benchmark/grid/cells.yaml")
    g.add_argument("--root", help="CloudBench root (default: auto-detect from cwd)")
    g.add_argument("--out", help="Where to write the app repo (default: <root>/gen_out)")
    g.add_argument("--records-dir", help="Where to write run records (default: <out>/_records)")
    g.add_argument("--no-case", action="store_true", help="Do not write the case file")
    g.add_argument("--force", action="store_true", help="Overwrite an existing case (the pin is preserved)")
    g.set_defaults(func=cmd_generate)

    c = sub.add_parser("catalog", help="Build/refresh the cloud service catalog (the supply side of the map)")
    c.add_argument("--provider", default="aws", choices=["aws"], help="Cloud provider (aws for now)")
    c.add_argument("--root", help="CloudBench root (default: auto-detect from cwd)")
    c.add_argument("--refresh", action="store_true", help="Rebuild and diff vs the stored catalog (the watcher)")
    c.add_argument("--dry-run", action="store_true", help="Build and summarise without writing the file")
    c.set_defaults(func=cmd_catalog)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
