# Cloud building blocks — start simple, add complexity

CloudBench tests **one cloud skill at a time**, then stacks them. If an agent cannot spin up a single server (B0), it will fail when the app also needs storage, a database, or a load balancer.

Two axes:

1. **Building blocks (B0–B6)** — what cloud pieces are involved (compute → storage → DB → …).
2. **Levels (L0–L5)** — how complex the overall topology is (matches `use_case_ladder` in CloudBot paper2).

## Building block taxonomy

| Block | Name | Cloud primitives | Typical repo signal | Maps to level |
|---|---|---|---|---|
| **B0** | Bare compute | EC2, SG, IAM, VPC refs | `run.sh`, no config | L0 |
| **B1** | Compute + runtime | B0 + user_data (JDK/Node) | `pom.xml`, `package.json` | L1 |
| **B2** | Object storage | B1 + S3 bucket + IAM policy | reads/writes `s3://` | L2 |
| **B3** | Stateful backing | B1 + RDS or ElastiCache | DB connection string in config | L3 |
| **B4** | Multi-tier | ALB + app tier + DB | web server + health check | L4 |
| **B5** | Event-driven | Lambda + SQS/SNS (+ S3 trigger) | serverless.yml, handler | L5 |
| **B6** | Infra-only | VPC/subnet/route without app | `infra_only` workload | special |

## Progression protocol (experiments)

1. Run all cases at **L1** (artifact tier) across blocks B0→B5 — no AWS cost.
2. Identify **first block where graph_match < threshold** (e.g. 80%).
3. Run **L3–L4 only on blocks at/above failure frontier** (cloud gated).
4. Record per-block pass rates for the paper's degradation curve.

## Case mapping (v1 corpus)

| Case | Block | Level | Repo |
|---|---|---|---|
| uc1 | B0 | 0 | `oodunsi1/cloudbot_uc1` |
| uc2 | B1 | 1 | `oodunsi1/cloudbot_uc2` |
| uc3 | B1 | 1 | `oodunsi1/cloudbot_uc3` |
| aws-s3-batch (published) | B2 | 2 | `cloudbench-aws-s3-batch` |
| aws-rds-api (generated, awaiting publish) | B3 | 3 | `cloudbench-aws-rds-api` |
| aws-alb-three-tier (planned) | B4 | 4 | `cloudbench-aws-alb-three-tier` |
| aws-lambda-queue (planned) | B5 | 5 | `cloudbench-aws-lambda-queue` |

> The full map (all ten kinds of work × building blocks × clouds, with coverage) lives in
> [`MAP.md`](MAP.md); the machine-readable grid is [`grid/cells.yaml`](grid/cells.yaml).

## Open improvement loop

When a block fails at L1, teams can use exported failure records ([`FAILURE_REGISTRY.md`](FAILURE_REGISTRY.md)) to improve agents, RAG, or repair — see [`TRAINING_LOOP.md`](TRAINING_LOOP.md).

---

## Boundaries

CloudBench measures deployment capability for **any** submitter. It is not a private training program for one agent. See [`PUBLIC_BOUNDARIES.md`](PUBLIC_BOUNDARIES.md).
