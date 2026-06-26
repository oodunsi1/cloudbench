# CloudBench — AWS ML inference service (B3, work-kind: mlai)

A small ML inference API (`app.py`, Flask): `POST /predict` returns a prediction from a model, `GET
/health` returns the marker `CLOUDBENCH_MLAI_OK`. The model is loaded from object storage when
`CLOUDBENCH_MODEL_URI` (an `s3://` URI) is set; otherwise a tiny bundled fallback is used. There is
**no infrastructure-as-code** in this repo — provisioning is the system under test's job.

## The task
Serve this inference API on AWS:
- provision compute (EC2 with a Python runtime) and an S3 bucket for the model,
- upload the model and set `CLOUDBENCH_MODEL_URI`,
- expose the service and let it serve predictions.

## How "it works" is proven
`GET /health` returns 200 with the marker `CLOUDBENCH_MLAI_OK`, and `POST /predict` with
`{"features": [..]}` returns a numeric `prediction`.

## Rules
- No IaC in this repo. No credentials in this repo (use the instance IAM role). The marker must be
  served verbatim.
