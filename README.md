# CloudBench — a repo-to-cloud deployment benchmark

CloudBench measures one thing end to end: **can a tool take a GitHub application
repository and get it running in the cloud — for real, and proven?** It looks at an app
repo, works out what cloud resources the app needs, produces the infrastructure, and
(at the higher tiers) deploys it, runs the app, checks it actually works, and tears it
down.

CloudBench is **agent-neutral**. Any model or agent can run it and submit scores.
[CloudBot](https://github.com/oodunsi1/cloudbot-paper2) is the **reference system** we
score first — it is not the only allowed entrant.

- **Model providers:** run **L1** on each release (no cloud cost) and report pass rate by service.
- **Researchers / agent builders:** compare custom agents, retrieval stacks, or ablations on the same pinned cases.

See [`benchmark/PUBLIC_VISION.md`](benchmark/PUBLIC_VISION.md) for the full goal and
[`benchmark/PUBLIC_BOUNDARIES.md`](benchmark/PUBLIC_BOUNDARIES.md) for what CloudBench does and does not claim.

---

## The dataset (cases)

Each case is its own **public application repo, pinned to an exact commit** — the app
only, with **no infrastructure-as-code**. Figuring out the infrastructure is the job of
the system under test.

**Two axes describe every case** (see [`benchmark/MAP.md`](benchmark/MAP.md) for the full version):

- **Workload — *what you run*.** The job the app does, one of ~10 kinds: `service` (always-on app/API),
  `batch` (run-to-finish job), `scheduled` (on a timer), `event` (reacts to a trigger), `streaming`
  (live data), `stateful` (a database/cache), `etl` (a data pipeline), `mlai` (an AI model), `static`
  (a static site), `composite` (a mix).
- **Building block — *what the cloud gives you to run it on*,** simple → complex: **B0** bare server ·
  **B1** + a language runtime · **B2** + object storage · **B3** + a database/cache · **B4** + a load
  balancer · **B5** serverless (functions + queues) · **B6** infra-only.

Think of it as the dish (workload) and the kitchen equipment (building block): a `batch` job may need
only B0, a `service` usually needs a database at B3. Each case is one workload × one block × one cloud.
(Don't confuse the block rung with the **evaluation tiers** L1–L4 below — those are how *deeply* a run
is graded, a different thing.)

The full corpus (generated from [`benchmark/grid/cells.yaml`](benchmark/grid/cells.yaml), the source of
truth — every case repo is public and pinned):

<!-- cases:start -->
| Case | Block | Workload | Cloud | Status | App repo |
|------|-------|----------|-------|--------|----------|
| `aws-ec2-wordcount` | B0 | batch | aws | ✅ covered | [cloudbench-aws-ec2-wordcount](https://github.com/oodunsi1/cloudbench-aws-ec2-wordcount) |
| `aws-ec2-java-image` | B1 | batch | aws | ✅ covered | [cloudbench-aws-ec2-java-image](https://github.com/oodunsi1/cloudbench-aws-ec2-java-image) |
| `aws-ec2-java-video` | B1 | batch | aws | ✅ covered | [cloudbench-aws-ec2-java-video](https://github.com/oodunsi1/cloudbench-aws-ec2-java-video) |
| `aws-ec2-webapi` | B1 | service | aws | ✅ covered | [cloudbench-aws-ec2-webapi](https://github.com/oodunsi1/cloudbench-aws-ec2-webapi) |
| `aws-scheduled-cron` | B1 | scheduled | aws | ✅ covered | [cloudbench-aws-scheduled-cron](https://github.com/oodunsi1/cloudbench-aws-scheduled-cron) |
| `aws-s3-batch` | B2 | batch | aws | ✅ covered | [cloudbench-aws-s3-batch](https://github.com/oodunsi1/cloudbench-aws-s3-batch) |
| `aws-static-cdn` | B2 | static | aws | ✅ covered | [cloudbench-aws-static-cdn](https://github.com/oodunsi1/cloudbench-aws-static-cdn) |
| `aws-elasticache-service` | B3 | service | aws | ✅ covered | [cloudbench-aws-elasticache-service](https://github.com/oodunsi1/cloudbench-aws-elasticache-service) |
| `aws-etl-pipeline` | B3 | etl | aws | ✅ covered | [cloudbench-aws-etl-pipeline](https://github.com/oodunsi1/cloudbench-aws-etl-pipeline) |
| `aws-mlai-inference` | B3 | mlai | aws | ✅ covered | [cloudbench-aws-mlai-inference](https://github.com/oodunsi1/cloudbench-aws-mlai-inference) |
| `aws-rds-api` | B3 | service | aws | ✅ covered | [cloudbench-aws-rds-api](https://github.com/oodunsi1/cloudbench-aws-rds-api) |
| `aws-stateful-store` | B3 | stateful | aws | ✅ covered | [cloudbench-aws-stateful-store](https://github.com/oodunsi1/cloudbench-aws-stateful-store) |
| `aws-alb-three-tier` | B4 | composite | aws | ✅ covered | [cloudbench-aws-alb-three-tier](https://github.com/oodunsi1/cloudbench-aws-alb-three-tier) |
| `aws-lambda-queue` | B5 | event | aws | ✅ covered | [cloudbench-aws-lambda-queue](https://github.com/oodunsi1/cloudbench-aws-lambda-queue) |
| `aws-streaming-kinesis` | B5 | streaming | aws | ✅ covered | [cloudbench-aws-streaming-kinesis](https://github.com/oodunsi1/cloudbench-aws-streaming-kinesis) |
| `gcp-static-site` | B2 | static | gcp | ✅ covered | [cloudbench-gcp-static-site](https://github.com/oodunsi1/cloudbench-gcp-static-site) |
| `azure-static-site` | B2 | static | azure | ✅ covered | [cloudbench-azure-static-site](https://github.com/oodunsi1/cloudbench-azure-static-site) |

_17 covered of 17 cases across 3 clouds (aws, gcp, azure). Generated from `benchmark/grid/cells.yaml` by `scripts/sync_docs.py` — do not edit between the markers._
<!-- cases:end -->

Case contracts live in [`benchmark/cases/`](benchmark/cases/); the full grid is in
[`benchmark/grid/`](benchmark/grid/) and explained in [`benchmark/MAP.md`](benchmark/MAP.md).

---

## Evaluation tiers

| Tier | What is measured | Cloud required |
|------|------------------|----------------|
| **L1** | Infrastructure graph + `terraform validate` | No |
| **L2** | `terraform plan` succeeds | Optional |
| **L3** | Apply + deployment proof | Yes (owner approval) |
| **L4** | Workload probes (the app actually ran: stdout, HTTP, etc.) | Yes (owner approval) |

L3–L4 cost real money and run real cloud resources — **never `terraform apply` without
explicit owner approval.** The cheap L1 tier is where broad coverage lives.

---

## Quick start

```bash
# Install the shared library the harness depends on (sibling checkout)
pip install -e ../cloudbot-paper2/cloudbot-common

# Install the harness
cd harness && pip install -e ".[dev]"

# Validate a case contract
bench validate ../benchmark/cases/aws-rds-api.yaml --require-pinned

# Score L1 artifacts from a run (no cloud apply)
bench score ../benchmark/cases/aws-ec2-wordcount.yaml --tier L1 \
  --archspec /path/to/archspec.json \
  --terraform-dir /path/to/terraform_runs/<slug>/<ts> \
  -o score.json
```

---

## Layout

| Path | Purpose |
|------|---------|
| [`benchmark/cases/`](benchmark/cases/) | Case contracts (pinned repo + expected resources + validation + teardown) |
| [`benchmark/grid/`](benchmark/grid/) | The workload × building-block × provider map + the AWS service catalog |
| [`benchmark/repos/`](benchmark/repos/) | Recipes + templates used to generate new case app repos |
| [`harness/`](harness/) | The `bench` command line tool: `validate`, `generate`, `score`, `catalog` |

## Key design docs

- [`benchmark/SCHEMA.md`](benchmark/SCHEMA.md) — the case contract + metrics
- [`benchmark/BUILDING_BLOCKS.md`](benchmark/BUILDING_BLOCKS.md) — the simple → complex cloud ladder
- [`benchmark/ASK_TYPES.md`](benchmark/ASK_TYPES.md) — how much is specified vs inferred (the difficulty spine)
- [`benchmark/LEADERBOARD.md`](benchmark/LEADERBOARD.md) — how to submit scores
- [`benchmark/FAILURE_REGISTRY.md`](benchmark/FAILURE_REGISTRY.md) — the shared failure-record format
- [`benchmark/NAMING.md`](benchmark/NAMING.md) — the `cloudbench-<provider>-<service>-<slug>` naming scheme
- [`benchmark/SERVICE_CATALOG.md`](benchmark/SERVICE_CATALOG.md) — AWS service coverage

## License

TBD — to be set alongside the CloudBot paper artifact release.
