# CloudBench service atlas (AWS v1)

Maps **cloud services** → **benchmark cases** → **status**. Extensible to GCP/Azure
later (`provider` prefix on each row).

> **This is the curated roadmap view (~20 services).** The *complete*, auto-generated, watched list
> of all services now lives in [`SERVICE_CATALOG.md`](SERVICE_CATALOG.md) +
> [`grid/services/aws.yaml`](grid/services/aws.yaml) (built by `bench catalog`). Use this atlas for
> the prioritised phase plan; use the catalog for "what exists and what's covered."

Legend: **live** = pinned case in [`cases/`](cases/); **planned** = designed, repo not published.

---

## Phase roadmap (public)

| Phase | Scope | Target |
|-------|--------|--------|
| **1** | B0–B1 building blocks | 3 live cases (EC2) |
| **2** | B2–B5 composed blocks | +4 cases (S3, RDS, ALB, Lambda/SQS) |
| **3** | One case per major service family | ~20–30 AWS services |
| **4** | Multi-service composed applications | Realistic migration scenarios |
| **5** | Complex production-style apps | Enterprise-grade workloads |

Phase 3+ grows the atlas incrementally; v1 paper ships Phase 1–2 design + Phase 1 results.

---

## Atlas table

| AWS service | Service family | Block | Case id | Display name | Status | Phase |
|-------------|----------------|-------|---------|--------------|--------|-------|
| EC2 | compute | B0 | uc1 / aws-ec2-wordcount | CloudBench AWS EC2 Wordcount | **live** | 1 |
| EC2 | compute | B1 | uc2 / aws-ec2-java-image | CloudBench AWS EC2 Java Image | **live** | 1 |
| EC2 | compute | B1 | uc3 / aws-ec2-java-video | CloudBench AWS EC2 Java Video | **live** | 1 |
| IAM | iam_role | B0–B1 | (shared) | — | live (in all EC2 cases) | 1 |
| Security Group | security_group | B0–B1 | (shared) | — | live (in all EC2 cases) | 1 |
| S3 | s3 | B2 | aws-s3-batch | CloudBench AWS S3 Batch | planned | 2 |
| RDS | rds | B3 | aws-rds-api | CloudBench AWS RDS API | planned | 2 |
| ALB | alb | B4 | aws-alb-three-tier | CloudBench AWS ALB Three-Tier | planned | 2 |
| Lambda | lambda | B5 | aws-lambda-queue | CloudBench AWS Lambda Queue | planned | 2 |
| SQS | sqs | B5 | aws-lambda-queue | (same case) | planned | 2 |

---

## Phase 3 candidates (not yet scheduled)

One canonical case per row when Phase 2 is stable:

| AWS service | Suggested case id | Notes |
|-------------|-------------------|-------|
| VPC | aws-vpc-network | B6 / networking block |
| EBS | aws-ebs-volume | Attach to EC2 |
| ElastiCache | aws-elasticache-api | Cache-backed API |
| DynamoDB | aws-dynamodb-api | NoSQL backing |
| SNS | aws-sns-notify | Pub/sub |
| CloudWatch | aws-cloudwatch-logs | Observability probe |
| Route53 | aws-route53-dns | DNS + health |
| ECS | aws-ecs-service | Container orchestration |
| EKS | aws-eks-workload | Kubernetes (long-term) |
| API Gateway | aws-apigw-lambda | Serverless API front |

---

## Multi-cloud (future)

| Provider | Example case id | Display name |
|----------|-----------------|--------------|
| GCP | gcp-gce-wordcount | CloudBench GCP GCE Wordcount |
| GCP | gcp-gcs-batch | CloudBench GCP GCS Batch |
| Azure | azure-vm-wordcount | CloudBench Azure VM Wordcount |
| Azure | azure-blob-batch | CloudBench Azure Blob Batch |

Same schema fields: `provider`, `primary_service`, `aws_services` (or `gcp_services`, etc.).

---

## How to read leaderboard coverage

For each submission, compute pass rate **per `primary_service`** row in this table.
A model can score 100% on EC2 and 0% on RDS — both facts matter.

Design details: [`LEADERBOARD.md`](LEADERBOARD.md).  
Repo naming: [`NAMING.md`](NAMING.md).
