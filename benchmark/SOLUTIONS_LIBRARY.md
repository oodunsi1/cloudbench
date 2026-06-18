# AWS Solutions Library — a source of use-case cases

> Plain-English companion to the auto-pulled index
> [`grid/sources/aws-solutions-library.yaml`](grid/sources/aws-solutions-library.yaml).

## What this is

AWS publishes a set of **vetted, ready-to-run "Guidance" / "Solution" repositories** — real-world
builds for popular business and technical needs, grouped on the AWS site by role (Cloud Architect,
Platform Engineer, AI Ops, App Developer) and shipped as open GitHub samples in the
[`aws-solutions-library-samples`](https://github.com/aws-solutions-library-samples) org.

They matter to CloudBench because they are exactly the **"use case"** rung of the inference spine
([`ASK_TYPES.md`](ASK_TYPES.md), level 4): you're given an *outcome* ("connected-vehicle platform",
"low-cost semantic search", "live streaming"), and the build has to work out *which* services deliver
it. Many also work as level-5 **`app-repo`** cases (here's the repo — deploy it).

## What we pulled

`gh api` over the org gives us a free, refreshable index — **321 solution repos** (317 active, 4
archived). Each row in [`grid/sources/aws-solutions-library.yaml`](grid/sources/aws-solutions-library.yaml)
holds: name, URL, description, main language, topics, stars, last-pushed date, and:

- `ask_type_candidate: use-case` — where it sits on the inference spine.
- `status: indexed` — it's **listed as a source**, not yet turned into a runnable benchmark case.

Languages skew to **Python (133)** and **TypeScript (55)**, then notebooks, JavaScript, Shell, and
**Terraform/HCL (14)** — so most are real application code, a good match for the repo-to-cloud task.

## How it fits the map

This is a **source**, like the service catalog is a source — a watched external list we draw cases
from. The flow:

```
index (this file)  →  pick a solution  →  turn it into a case (ask_type: use-case or app-repo)
                                          →  the engine/CloudBot attempts it  →  errors feed learning
```

So the corpus now grows from three places: **per-service** (the service catalog), **per-use-case**
(this Solutions Library), and the **hand-built diagonal** (uc1–uc3, aws-s3-batch, …) — all tagged by
how they're asked.

## Out of scope (for now)

We only **indexed** the repos. We have not cloned them, judged which deploy cleanly, or scraped the
AWS web pages for the persona/use-case grouping and "time to complete" — those are later steps when we
start turning specific solutions into runnable cases.

## Refreshing

Re-pull with `gh api 'orgs/aws-solutions-library-samples/repos?per_page=100' --paginate` and rebuild
the index (the same step that created it). A future `bench catalog --source solutions` can fold this
into the watcher.
