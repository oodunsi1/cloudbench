# CloudBench — naming

## Benchmark name

**CloudBench** — the benchmark program and paper.  
**CloudBot** — the reference agent we test first (not part of the benchmark name).

Full paper title: *CloudBench: An Execution-Based Benchmark for Repository-to-Cloud Deployment*

---

## Case naming — provider + service + workload

Names should read like a product label: **what cloud**, **what service**, **what app**.

### Pattern

| Layer | Format | Example |
|-------|--------|---------|
| **Display name** | `CloudBench {Provider} {Service} {Workload}` | CloudBench AWS EC2 Wordcount |
| **Case id** | `{provider}-{service}-{slug}` | `aws-ec2-wordcount` |
| **GitHub repo** | `cloudbench-{provider}-{service}-{slug}` | `cloudbench-aws-ec2-wordcount` |
| **YAML tags** | `provider`, `primary_service`, `building_block` | aws, ec2, B0 |

### Why this shape

- **Intuitive** — you see EC2 vs S3 vs RDS at a glance.
- **Multi-cloud ready** — swap provider prefix later without renaming the scheme:
  - `gcp-gce-wordcount` → CloudBench GCP GCE Wordcount
  - `azure-vm-wordcount` → CloudBench Azure VM Wordcount
- **Building block visible** — service name maps to the ladder (EC2 = compute block, S3 = storage, etc.).

### AWS v1 case map

| Block | Display name | Case id | Repo (target) | Legacy repo (v0) |
|-------|--------------|---------|---------------|------------------|
| B0 | CloudBench AWS EC2 Wordcount | `aws-ec2-wordcount` | `cloudbench-aws-ec2-wordcount` | `cloudbot_uc1` |
| B1 | CloudBench AWS EC2 Java Image | `aws-ec2-java-image` | `cloudbench-aws-ec2-java-image` | `cloudbot_uc2` |
| B1 | CloudBench AWS EC2 Java Video | `aws-ec2-java-video` | `cloudbench-aws-ec2-java-video` | `cloudbot_uc3` |
| B2 | CloudBench AWS S3 Batch | `aws-s3-batch` | `cloudbench-aws-s3-batch` | (planned) |
| B3 | CloudBench AWS RDS API | `aws-rds-api` | `cloudbench-aws-rds-api` | (planned) |
| B4 | CloudBench AWS ALB Three-Tier | `aws-alb-three-tier` | `cloudbench-aws-alb-three-tier` | (planned) |
| B5 | CloudBench AWS Lambda Queue | `aws-lambda-queue` | `cloudbench-aws-lambda-queue` | (planned) |

Legacy `uc1`–`uc3` ids stay in YAML until repos are renamed; `name` and new fields carry the intuitive label.

### Multi-cloud (future)

Same pattern, different provider prefix:

```
cloudbench-gcp-gcs-batch      → CloudBench GCP GCS Batch
cloudbench-azure-blob-batch   → CloudBench Azure Blob Batch
cloudbench-aws-ec2-wordcount  → CloudBench AWS EC2 Wordcount  (v1)
```

Case YAML adds `provider: aws|gcp|azure` and `primary_service: ec2|s3|rds|...`.

### What lives where

| Repo | Holds |
|------|--------|
| `cloudbot-benchmarking` | Case YAML, harness, paper, literature |
| `cloudbench-aws-*` | One application per repo |
| `cloudbot-paper2` | CloudBot pipeline (system under test) |

---

## Two different “Terraformer” things (do not confuse)

| Name | What it is | Relation to CloudBench |
|------|------------|------------------------|
| **TerraFormer** (paper, arXiv 2601.08734) | LLM system fine-tuned to **generate/mutate Terraform** from text; evaluated on IaC-Eval | **Method** — how to build a better IaC model; not a repo-to-cloud benchmark |
| **terraformer** (Google Cloud OSS tool) | CLI that **imports existing cloud resources → Terraform files** (reverse IaC) | **Tool** — opposite direction (infra → code); useful for golden references, not our eval path |

CloudBench measures **app repo → new cloud deployment**, not NL→TF generation alone and not import-from-existing-infra.

---

## Collision check

- “CloudBench” used by unrelated DB/analytics tools — disambiguate with full paper title.
- No published benchmark uses **CloudBench AWS EC2**-style naming for repo-to-cloud deployment.
