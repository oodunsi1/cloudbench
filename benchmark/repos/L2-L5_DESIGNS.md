# L2–L5 application repo designs

One GitHub repo per case. Names follow [`NAMING.md`](../NAMING.md):  
**CloudBench {Provider} {Service} {Workload}** → `cloudbench-{provider}-{service}-{slug}`.

## aws-s3-batch (B2)

| Field | Value |
|-------|-------|
| Display | CloudBench AWS S3 Batch |
| Case id | `aws-s3-batch` |
| Repo | `cloudbench-aws-s3-batch` |

**App:** Python reads `input.txt` from S3, writes word counts to `s3://<bucket>/output/result.json`.

```
README.md
requirements.txt
process.py
config.yml
run.sh
```

**Services:** EC2 + S3 + IAM/SG  
**Pin:** tag `cloudbench-v1.0.0`

---

## aws-rds-api (B3)

| Field | Value |
|-------|-------|
| Display | CloudBench AWS RDS API |
| Case id | `aws-rds-api` |
| Repo | `cloudbench-aws-rds-api` |

**App:** Flask `GET /health` + Postgres (`db/init.sql`).

**Services:** EC2 + RDS + IAM/SG  
**Probe:** HTTP 200 on `/health`

---

## aws-alb-three-tier (B4)

| Field | Value |
|-------|-------|
| Display | CloudBench AWS ALB Three-Tier |
| Case id | `aws-alb-three-tier` |
| Repo | `cloudbench-aws-alb-three-tier` |

**App:** Static front + Flask API + RDS (ALB → EC2 → RDS).

**Probe:** ALB health check + JSON API response

---

## aws-lambda-queue (B5)

| Field | Value |
|-------|-------|
| Display | CloudBench AWS Lambda Queue |
| Case id | `aws-lambda-queue` |
| Repo | `cloudbench-aws-lambda-queue` |

**App:** S3 upload → Lambda → SQS → worker Lambda (CloudWatch log proof).

**Services:** Lambda + SQS + S3 + IAM

---

## Multi-cloud (later)

| Display | Repo |
|---------|------|
| CloudBench GCP GCS Batch | `cloudbench-gcp-gcs-batch` |
| CloudBench Azure Blob Batch | `cloudbench-azure-blob-batch` |

Same app logic; `provider` and `primary_service` change in case YAML.

## Order

1. `aws-s3-batch`
2. `aws-rds-api`
3. `aws-alb-three-tier`
4. `aws-lambda-queue`
