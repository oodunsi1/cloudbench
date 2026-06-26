# CloudBench — AWS streaming consumer (B5, work-kind: streaming)

A streaming worker (`consumer.py`): it consumes records from a Kinesis stream and processes each one,
emitting `CLOUDBENCH_STREAM_OK`. There is **no infrastructure-as-code** in this repo — provisioning is
the job of the system under test.

## The task
Run this consumer on AWS:
- provision a Kinesis data stream and compute (EC2 + Python),
- grant the instance an IAM role with read access to the stream,
- set `CLOUDBENCH_STREAM` to the stream name and run `./run.sh`.

## How "it works" is proven
The consumer connects to the stream, reads records, exits 0, and emits `CLOUDBENCH_STREAM_OK`.

## Rules
- No IaC in this repo. No credentials in this repo. The marker must be emitted verbatim.
