# The CloudBench map

> Plain-English companion to [`grid/cells.yaml`](grid/cells.yaml) (the machine-readable version).
> If the two ever disagree, `cells.yaml` is the source of truth and this file should be updated.

## The one big idea

CloudBench sits between **two lists, and both are countable.** That is the whole point — there is no
"infinite space" to fight, just a finite grid to fill.

**List 1 — what people run.** Everything anyone runs in the cloud falls into about **ten kinds**:

| Kind of work | Plain meaning | Example |
|---|---|---|
| service | long-running web apps, APIs, microservices, app backends, game servers | a website that's always up |
| batch | run-to-completion jobs: data / image / video processing, reports | count the words in a file |
| scheduled | jobs that run on a clock | a nightly report |
| event | event-driven / async: queues, pub/sub, serverless triggers | "a file landed → process it" |
| streaming | real-time, continuous data | live clicks or sensor feeds |
| stateful | databases, caches, object & vector stores | the place data lives |
| etl | data pipelines: extract, transform, load | move + reshape data |
| mlai | ML / AI: training, inference, model serving, RAG, agent runtimes | answer with a model |
| static | static content / CDN | a docs site served fast |
| composite | multi-tier apps that combine the above | web + API + database together |

**List 2 — what the cloud gives you.** Each cloud has a big-but-finite, slowly-growing set of
**building blocks**, which we order simple → complex:

| Block | What it adds |
|---|---|
| B0 | bare compute (a single server) |
| B1 | compute + a language runtime (Java, Node…) |
| B2 | + object storage (S3) |
| B3 | + a database or cache |
| B4 | multiple tiers + a load balancer |
| B5 | event-driven serverless (functions + queues) |
| B6 | infrastructure only, no app (special) |

**Clouds, in order:** AWS first, then Google, then Microsoft, then Alibaba.

**The real supply list.** Building blocks B0–B6 are the *coarse* view. The *complete* supply side —
every named service each cloud sells, grouped by category — is the **service catalog**
([`SERVICE_CATALOG.md`](SERVICE_CATALOG.md)). For AWS that's **426 services** today, auto-built and
kept current by `bench catalog`. Each service is a corpus item that will get its own run-as-is repo;
the value is in combining them into the ten kinds of work.

**How it's asked (the main difficulty axis).** On top of *what runs* and *what's offered*, each case
also has a **way it's handed over** — from "build this exact service" up to "here's an app, infer
everything." That spectrum, ordered by how much the system must work out for itself, is the
benchmark's **primary difficulty spine** ([`ASK_TYPES.md`](ASK_TYPES.md)): `explicit-instruction` →
`single-service` → `service-group` → `use-case` → `app-repo` → `infer-from-app`. Every case we have
today is `app-repo`. The **use-case** rung draws on AWS's own solution repos
([`SOLUTIONS_LIBRARY.md`](SOLUTIONS_LIBRARY.md), 321 indexed).

So every benchmark case is **one spot** where a *kind of work* meets a *building block* meets a
*cloud* — handed over at a given *ask-type*.

## How the two lists connect (kind of work to building block)

The two lists above are not independent. Each kind of work has a **natural rung**: the smallest set of
building blocks it needs to run. This table makes that link explicit (the machine-readable source is
[`grid/cells.yaml`](grid/cells.yaml)).

| Kind of work | B0 bare | B1 +runtime | B2 +storage | B3 +database | B4 +load balancer | B5 serverless |
|---|---|---|---|---|---|---|
| **batch** | ✅ wordcount | ✅ java image/video | ✅ s3-batch | | | |
| **service** | | | | ✅ rds-api | | |
| **composite** | | | | | ✅ alb-three-tier | |
| **event** | | | | | | ✅ lambda-queue |
| **scheduled** | | ✅ scheduled-cron | | | | |
| **static** | | | ✅ static-cdn | | | |
| **stateful** | | | | ✅ stateful-store | | |
| **etl** | | | | ✅ etl-pipeline | | |
| **mlai** | | | | ✅ mlai-inference | | |
| **streaming** | | | | | | ✅ streaming-kinesis |

Legend: ✅ filled (real, published, pinned) · ⏳ next · 📋 planned · ▫ natural home, not yet scheduled.
**All ten kinds of work now have at least one covered case** (the first full pass of the demand axis).

Why each kind lands where it does:

1. **batch** needs only a server, then a runtime, then object storage, so it climbs B0, B1, B2.
2. **service** (a request-answering API) needs a database behind it, so its home is B3.
3. **composite** (a multi-tier app) needs a load balancer to route between tiers, so its home is B4.
4. **event** work (a trigger fires, then work runs) maps to serverless functions plus a queue, so B5.

The diagonal fill order below is one step down-and-across this table: a different kind of work on each
higher rung, so a few cases span the whole range.

## One map, two jobs

There is a single finite map. **This benchmark is the scorecard** — it proves each spot actually
runs. **The "AI in the cloud" system (CloudBot) is the thing that fills the spots.** Same map, two
jobs. The public benchmark lives here; the private vision stays out of these files.

## How we fill it: a diagonal first

We can't fill everything at once, so we pick an order. The first order is a **diagonal across AWS** —
one spot per rung, climbing easy → hard, each rung a different kind of work. It's the cheapest way to
a cross-section that spans the whole range.

| Rung (easy→hard) | Building block | Kind of work | Case | Status |
|---|---|---|---|---|
| L0 | bare compute | batch | `uc1` (aws-ec2-wordcount) | ✅ real + pinned |
| L1 | + runtime | batch (image/video) | `uc2`, `uc3` | ✅ real + pinned |
| L2 | + object storage | batch + storage | `aws-s3-batch` | ✅ published |
| L3 | + database | long-running service / API | `aws-rds-api` | ✅ published + pinned |
| L4 | + load balancer | composite multi-tier | `aws-alb-three-tier` | ✅ published + pinned |
| L5 | serverless events | event-driven | `aws-lambda-queue` | ✅ published + pinned |

## Where coverage stands (AWS)

Reading: ✅ filled · ⏳ next · 📋 planned · ▫ empty (drawn, not scheduled) · — not a natural fit.

| Kind of work ↓ \ Block → | B0 | B1 | B2 | B3 | B4 | B5 |
|---|----|----|----|----|----|----|
| batch | ✅ | ✅ | ✅ | | | |
| service | | | | ✅ | | |
| composite | | | | | ✅ | |
| event | | | | | | ✅ |
| scheduled | | ✅ | | | | |
| static | | | ✅ | | | |
| stateful | | | | ✅ | | |
| etl | | | | ✅ | | |
| mlai | | | | ✅ | | |
| streaming | | | | | | ✅ |

**Count: 13 spots filled across all 10 kinds of work** — every demand-axis kind now has at least one
real, published, pinned, validating case on AWS (batch ×4 at B0–B2; service, stateful, etl, mlai at B3;
static at B2; scheduled at B1; composite at B4; event, streaming at B5). The first full pass of the
demand axis is complete. Google / Microsoft / Alibaba are the same grid again, not started.

**Service-catalog coverage:** 3 of 426 AWS services are the focus of a runnable repo so far — `ec2`
(uc1–uc3), `s3` (aws-s3-batch), `rds` (aws-rds-api). See [`SERVICE_CATALOG.md`](SERVICE_CATALOG.md).

## How the engine uses this

`bench generate --cell <id>` looks the cell up in [`grid/cells.yaml`](grid/cells.yaml), copies the
matching **recipe** (see [`repos/RECIPE.md`](repos/RECIPE.md)), writes the app repo + the case file,
and checks its own output before marking the cell ready. The cell marked `next: true` is the one it
fills first.
