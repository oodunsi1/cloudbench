# CloudBench AWS S3 Batch

A tiny **run-to-completion batch job**: it reads a text file from an S3 bucket, counts the words,
and writes the result back to the same bucket as JSON.

This repository is a **CloudBench benchmark case** (building block **B2** — compute plus object
storage). It is the *application*, not the infrastructure: there is deliberately **no Terraform or
other infrastructure-as-code here**. Figuring out the cloud resources this app needs, creating them,
running the app, and proving it worked is the job of the repository-to-cloud system being tested.

## What it does

```
input   s3://<bucket>/input.txt              a plain-text file
output  s3://<bucket>/output/result.json     { "word_counts": {...}, "total_words": N }
```

## Cloud resources it needs

| Resource | Why |
|---|---|
| A compute instance (e.g. EC2) | runs `run.sh` |
| An IAM role / instance profile | grants the instance `s3:GetObject` + `s3:PutObject` on the bucket |
| A security group | basic egress so the instance can reach S3 |
| An S3 bucket | holds `input.txt` and receives `output/result.json` |

No credentials are stored in this repo — the app relies on the instance's IAM role.

## How to run

```bash
export CLOUDBENCH_BUCKET=<the provisioned bucket name>
./run.sh
```

`run.sh` installs `requirements.txt` and runs `process.py`. On success it prints the output
location, e.g. `Wrote word counts to s3://my-bucket/output/result.json`.

### Configuration

`config.yml` holds the defaults; every value can be overridden by an environment variable:

| Setting | Env var | Default |
|---|---|---|
| bucket | `CLOUDBENCH_BUCKET` | _(required)_ |
| input object key | `CLOUDBENCH_INPUT_KEY` | `input.txt` |
| output object key | `CLOUDBENCH_OUTPUT_KEY` | `output/result.json` |
| region | `AWS_REGION` | `us-east-1` |

## Success criteria (validation contract)

A run is successful when:

- `process.py` exits `0`,
- stdout contains the output `s3://…` URI, and
- the object `output/result.json` exists in the bucket.

## Local development

The word-count logic and the S3 read/write round-trip are exercised with an in-memory fake S3
(no AWS account, no `moto`):

```bash
python -m pip install -r requirements.txt pytest
python -m pytest
```
