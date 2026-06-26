# CloudBench — AWS stateless web API (B1, work-kind: service)

A small stateless HTTP service (`app.py`, Flask): `GET /health` returns the marker
`CLOUDBENCH_WEBAPI_OK`, `POST /echo` echoes its JSON body. No database — it just needs to be reachable.
There is **no infrastructure-as-code** in this repo — provisioning is the system under test's job.

## The task
Serve this API on AWS: provision compute (EC2 + Python), expose the app's port, and make `/health`
reachable.

## How "it works" is proven
`GET /health` returns 200 with the marker `CLOUDBENCH_WEBAPI_OK`.

## Rules
- No IaC in this repo. No credentials in this repo. The marker must be served verbatim.
