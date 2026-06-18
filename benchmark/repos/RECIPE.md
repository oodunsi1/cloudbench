# Recipes — how one spot on the map gets filled

> A **recipe** is the blueprint for one benchmark cell. The engine (`bench generate`) reads a recipe
> and turns it into two things: an **app repo** (the code a tool will be asked to deploy) and a
> **case file** (what the harness scores the attempt against). Then it checks its own work.

## Why recipes exist

The map ([`../MAP.md`](../MAP.md)) has many spots to fill. Filling each one by hand would be slow and
inconsistent. A recipe captures, once, everything needed to build a spot of a given **archetype** (a
reusable shape, e.g. "a batch job that reads and writes object storage"). The engine then stamps out
the spot — and can stamp out siblings (the same shape on another cloud, or a hold-out twin in another
language) by changing a couple of fields.

This is the **recipe-first** rule: build one spot fully by hand, capture it as a recipe, *then* let
the engine reproduce the pattern. The first recipe — [`recipes/aws-s3-batch.yaml`](recipes/aws-s3-batch.yaml) —
is the worked example, taken from the already-published
[`cloudbench-aws-s3-batch`](https://github.com/oodunsi1/cloudbench-aws-s3-batch) cell.

## What a recipe contains

| Field | Plain meaning |
|---|---|
| `cell` | which spot on the map this fills (matches an id in [`../grid/cells.yaml`](../grid/cells.yaml)) |
| `archetype` | the reusable shape, so siblings can share it |
| identity (`display_name`, `repo_name`, `provider`, `primary_service`, `building_block`, `level`) | names + where it sits on the map (follows [`../NAMING.md`](../NAMING.md)) |
| `runtime.language` | what the app is written in |
| `needs_service_families` / `aws_services` | the cloud building blocks the app needs — the harness scores a tool's design against this |
| `success_check` | how we know the app actually ran (stdout text, an object that must exist, an HTTP 200…) |
| `teardown_check` | how we confirm nothing is left running afterward |
| `app_files` | the files to write; their contents live as templates in [`templates/<archetype>/`](templates/) |
| `constraints` | rules the app must obey (no infra code in the repo, no secrets, config injected at runtime) |

## What the engine does with it

```
bench generate --cell <id>
  1. find the cell in grid/cells.yaml, then its recipe in repos/recipes/<id>.yaml
  2. copy the template files  →  gen_out/<id>/        (the app repo)
  3. build the case file from the recipe fields  →  benchmark/cases/<id>.yaml
  4. validate the case (validate_cloudbench_case) — refuse to finish if it fails
  5. write a run record (which cell, did it work, where it tripped)
```

The app repo is then reviewed and, on approval, published to its own GitHub repo and pinned —
exactly how `aws-s3-batch` was done.

## Adding a new archetype

When the next spot is a new shape (e.g. "web service + database" for `aws-rds-api`), author a new
recipe and a new `templates/<archetype>/` folder by hand first (recipe-first), then run the engine to
materialise it. Cells that share an existing archetype need only a new recipe file pointing at the
same template.
