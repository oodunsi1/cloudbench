# How it's asked — the inference spine

> The benchmark's **main difficulty axis**. Every case is tagged with an `ask_type`. The other lenses
> (the workload buckets in [`MAP.md`](MAP.md), the building-block ladder in
> [`BUILDING_BLOCKS.md`](BUILDING_BLOCKS.md), the service catalog in [`SERVICE_CATALOG.md`](SERVICE_CATALOG.md))
> ride underneath this one.

## The idea

There isn't one kind of benchmark task. There's a **spectrum of how the job is handed over** — from
"do exactly this" to "here's an app, figure everything out." The thing that makes it harder is **how
much the system must work out for itself**. We order the spectrum by that, and call it the *ask-type*.

This is the same idea as the **"What goes in"** column in
[`../literature/related-work-matrix.md`](../literature/related-work-matrix.md): every other benchmark
sits at a *single* point on this spectrum. CloudBench is built to **span all six**.

## The six ask-types (most explicit → most inferred)

| # | Ask-type | What goes in | What the system must infer | Example | Source of cases |
|---|----------|--------------|----------------------------|---------|-----------------|
| 1 | `explicit-instruction` | a precise spec | nothing — just do it | "Build an ECS service with this image, 2 tasks, this port." | hand-written |
| 2 | `single-service` | one service to stand up | the minimal wrapper to run it | "Run an S3 bucket I can read/write." | the service catalog (one per service) |
| 3 | `service-group` | a few services together | how they connect | "Stand up an API on EC2 with an RDS database." | combinations of catalog services |
| 4 | `use-case` | an outcome, not the parts | *which* services achieve it | "Build a secure multi-account foundation." | **AWS Solutions Library** (see [`SOLUTIONS_LIBRARY.md`](SOLUTIONS_LIBRARY.md)) |
| 5 | `app-repo` | a GitHub app repository | what the code needs, then deploy it | "Here's this repo — deploy it and prove it runs." | **where CloudBench is today** (uc1–uc3, aws-s3-batch, …) |
| 6 | `infer-from-app` | just a running application | *everything* — services, wiring, config | "Here's an app. Make it run in the cloud." | the **north star** |

## Why order it this way

Level 1 asks the system to **obey**; level 6 asks it to **understand and decide**. As you climb, more
of the answer has to come from the system, not the prompt. So the headline result is simple to state:
**how does success drop as the ask gets vaguer?** Today's tools can probably stand up one service
(level 1–2); the open question is how far up the ladder they hold.

`CloudBot = the know-how; CloudBench = the map.` This axis is the map's measure of *how much know-how
the task demands*.

## How cases are tagged

Each case file carries an optional `ask_type` field (one of the six ids above). Today every published
case is `app-repo` (level 5) — you hand over a repo and the system infers + deploys. As we add cases
from the service catalog (levels 2–3) and the Solutions Library (level 4), and eventually strip the
instructions away (level 6), the benchmark fills out the full spectrum.
