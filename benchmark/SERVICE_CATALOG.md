# The service catalog — the supply side of the map

> Plain-English companion to the auto-generated data in
> [`grid/services/aws.yaml`](grid/services/aws.yaml). Build/refresh it with `bench catalog`.

## What this is

The map has two sides. The **demand** side is the ten kinds of work people run (see [`MAP.md`](MAP.md)).
This file is the **supply** side: the **complete list of services a cloud actually sells** — the same
list you see under "All services" in the AWS console, organised by the same **category groups**
(Compute, Storage, Database, …).

It is generated, not hand-typed: `bench catalog` reads the service list straight from the AWS SDK
(`botocore`, already installed) — **free, offline, and versioned** — and writes one row per service
with its real name, its category, the repo it will eventually get, and whether it's covered yet. Today
that's **426 AWS services**.

## Why it's a corpus, not just an index

The goal is **one run-as-is GitHub repo per service** — a small, real thing that uses that service.
Many services are low-value on their own; the real value (and the hard part to measure) is
**combining** them into the ten kinds of work. So the order is: standalone per-service repos first,
combinations on top. Every run — success or failure — feeds CloudBot's error-learning.

**`CloudBot = the know-how. CloudBench = the map.`** CloudBench says *what exists* and *what's been
proven to run*; CloudBot is the system that figures out *how* to build and deploy each one.

## The watcher (keeping the list current)

The service list grows over time. `bench catalog --refresh` rebuilds the list and **diffs it against
the stored file**, reporting which services were **added** or **removed** since last time. That's the
watcher — realised for AWS today, for free. The same approach extends to Google, Microsoft, and
Alibaba through their own SDKs (designed, not built yet).

## What each row holds (`grid/services/aws.yaml`)

| Field | Plain meaning |
|---|---|
| `id` | the service's short SDK name (e.g. `s3`, `ec2`, `rds`) |
| `name` | the full product name (e.g. "Amazon Simple Storage Service") |
| `category` | which console group it belongs to (or `uncategorised`, filled in over time) |
| `target_repo` | the run-as-is repo it will get, named per [`NAMING.md`](NAMING.md) (`cloudbench-aws-<id>`) |
| `status` | `empty` (no repo yet) · `generated` (built locally) · `covered` (published + pinned) |
| `cell` | if covered/generated, the map cell it links to (e.g. `s3` → `aws-s3-batch`) |

## Coverage today

Of **426** AWS services, **3** are the focus of a runnable repo so far — `ec2` (the uc1–uc3 batch
jobs), `s3` (aws-s3-batch, published), and `rds` (aws-rds-api, generated). The rest are `empty`: the
map is fully drawn, and now gets filled service by service.

About 185 of the 426 are sorted into their category group from a seed mapping; the remainder are
`uncategorised` and get tidied as the catalog is maintained — exactly the kind of gap the watcher
makes visible.

## Relationship to the other docs

- [`SERVICE_ATLAS.md`](SERVICE_ATLAS.md) — the older hand-curated **roadmap** view (~20 services, with
  phases). This catalog is the complete, auto-generated, watched version it was the seed for.
- [`BUILDING_BLOCKS.md`](BUILDING_BLOCKS.md) — the coarse B0–B6 complexity ladder; a different lens on
  the same services.
- [`MAP.md`](MAP.md) — the demand side (kinds of work) and how the diagonal gets filled.
