# CloudBench — AWS event-driven queue worker (B5, work-kind: event)

An event-driven worker (`handler.py`): an AWS Lambda handler triggered by SQS. For each message it does
a tiny unit of work and emits the marker `CLOUDBENCH_EVENT_OK`. There is **no infrastructure-as-code**
in this repo — provisioning is the job of the system under test.

## The task
Deploy this as a serverless event consumer on AWS:
- create an SQS queue,
- package `handler.py` as a Lambda function (handler = `handler.handler`),
- wire the queue as the Lambda's event source, with an IAM role granting it queue access.

## How "it works" is proven
Send a message to the queue; the Lambda is invoked and processes it. It passes when the function runs
successfully and emits the marker `CLOUDBENCH_EVENT_OK` (in the response / logs). `python handler.py`
runs a local smoke test with a synthetic SQS event.

## Rules
- No IaC in this repo. No credentials in this repo (use the Lambda execution role). The marker must be
  emitted verbatim.
