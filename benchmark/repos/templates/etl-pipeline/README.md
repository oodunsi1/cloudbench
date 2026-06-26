# CloudBench — AWS ETL pipeline (B3, work-kind: etl)

A small ETL pipeline (`pipeline.py`): **extract** records from object storage, **transform** (aggregate
amounts per category), **load** the result into a key-value store. It emits `CLOUDBENCH_ETL_OK`. There
is **no infrastructure-as-code** in this repo — provisioning is the system under test's job.

## The task
Run this pipeline on AWS:
- provision compute (EC2 + Python), a source S3 bucket, and a sink DynamoDB table,
- set `CLOUDBENCH_INPUT_URI` (s3://...) and `CLOUDBENCH_TABLE`, grant access via the instance IAM role,
- run `./run.sh`.

## How "it works" is proven
The run exits 0 and emits `CLOUDBENCH_ETL_OK`, and the aggregated rows are written to the table.

## Rules
- No IaC in this repo. No credentials in this repo. The marker must be emitted verbatim.
