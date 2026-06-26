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
the system under test. Cases climb a difficulty ladder of cloud **building blocks**
(B0 = bare compute → B5 = serverless + queue).

| Case | Block | What it adds | Workload | Status | App repo |
|------|-------|--------------|----------|--------|----------|
| `uc1` | B0 | bare compute | batch job | ✅ pinned | [cloudbench-aws-ec2-wordcount](https://github.com/oodunsi1/cloudbench-aws-ec2-wordcount) |
| `uc2` | B1 | + language runtime | batch job | ✅ pinned | [cloudbench-aws-ec2-java-image](https://github.com/oodunsi1/cloudbench-aws-ec2-java-image) |
| `uc3` | B1 | + language runtime | batch job | ✅ pinned | [cloudbench-aws-ec2-java-video](https://github.com/oodunsi1/cloudbench-aws-ec2-java-video) |
| `aws-s3-batch` | B2 | + object storage (S3) | batch job | ✅ pinned | [cloudbench-aws-s3-batch](https://github.com/oodunsi1/cloudbench-aws-s3-batch) |
| `aws-rds-api` | B3 | + managed database (RDS) | web service | ✅ pinned | [cloudbench-aws-rds-api](https://github.com/oodunsi1/cloudbench-aws-rds-api) |
| `aws-alb-three-tier` | B4 | + load balancer | web service | 🛠 planned | — |
| `aws-lambda-queue` | B5 | serverless + queue | event worker | 🛠 planned | — |

Case contracts live in [`benchmark/cases/`](benchmark/cases/); the full grid of
workload-kind × building-block × provider is in [`benchmark/grid/`](benchmark/grid/) and
explained in [`benchmark/MAP.md`](benchmark/MAP.md).

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
