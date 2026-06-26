# CloudBench — AWS stateful key-value store (B3, work-kind: stateful)

A small stateful worker (`app.py`): it round-trips a record through a key-value store (writes an item,
reads it back, checks it matches) to prove persistence works. There is **no infrastructure-as-code**
in this repo — provisioning the store is the job of the system under test.

## The task
Run this worker against a provisioned AWS key-value store:
- provision compute (EC2 with a Python runtime) and a DynamoDB table,
- grant the instance an IAM role with access to the table,
- set `CLOUDBENCH_TABLE` to the table name and run `./run.sh`.

## How "it works" is proven
`./run.sh` runs `app.py`, which writes and reads back a record. It passes when the run exits 0 and the
output contains `CLOUDBENCH_STATEFUL_OK` (proving the store persisted and returned the record).

## Rules
- No IaC in this repo. No credentials in this repo (use the instance IAM role). The table name is
  injected at runtime. The marker `CLOUDBENCH_STATEFUL_OK` must be emitted verbatim.
