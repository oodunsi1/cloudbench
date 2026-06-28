# Cloud building blocks — start simple, add complexity

CloudBench tests **one cloud skill at a time**, then stacks them. If an agent cannot spin up a single server (B0), it will fail when the app also needs storage, a database, or a load balancer.

Three things get named in CloudBench — keep them distinct (they are NOT the same):

1. **Building block (B0–B6)** — *what cloud pieces are involved* (compute → +storage → +database →
   +load balancer → serverless). The rungs of a simple→complex ladder. (`cells.yaml`'s `level: 0–5` is
   just the rung number of block B0–B5 — the same ladder, not a separate axis.)
2. **Kind of work / workload** — *the job the app does* (service, batch, scheduled, event, streaming,
   stateful, etl, mlai, static, composite). This is the real second axis, crossed with the blocks; the
   full grid (workload × block × cloud) is in [`MAP.md`](MAP.md).
3. **Evaluation tier (L1–L4)** — *how deeply a run is graded* (L1 validate → L2 plan → L3 deploy → L4
   workload probes). A DIFFERENT "L" from the block rung — don't conflate them.

## Building block taxonomy

| Block | Name | Cloud primitives | Typical repo signal | Ladder rung |
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

## Case mapping (the corpus)

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

> The full map (all ten kinds of work × building blocks × clouds, with coverage) lives in
> [`MAP.md`](MAP.md); the machine-readable grid is [`grid/cells.yaml`](grid/cells.yaml).

## Open improvement loop

When a block fails at L1, teams can use exported failure records ([`FAILURE_REGISTRY.md`](FAILURE_REGISTRY.md)) to improve agents, RAG, or repair — see [`TRAINING_LOOP.md`](TRAINING_LOOP.md).

---

## Boundaries

CloudBench measures deployment capability for **any** submitter. It is not a private training program for one agent. See [`PUBLIC_BOUNDARIES.md`](PUBLIC_BOUNDARIES.md).
