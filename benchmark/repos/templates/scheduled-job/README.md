# CloudBench — AWS scheduled job (B1, work-kind: scheduled)

A small recurring job (`job.py`): each run appends a heartbeat line with the marker
`CLOUDBENCH_CRON_OK` and a UTC timestamp to `output/heartbeat.log`. There is **no
infrastructure-as-code** in this repo — provisioning and scheduling are the job of the system under
test.

## The task
Run this job on a schedule on AWS:
- provision compute (EC2 with a Python runtime, or a serverless equivalent),
- install the app and schedule it (cron, systemd timer, or EventBridge),
- let at least one scheduled tick fire.

## How "it works" is proven
A scheduled tick runs `./run.sh`, which executes `job.py`. It passes when the run exits 0 and the
output contains the marker `CLOUDBENCH_CRON_OK` (proving a tick fired and the job ran).

## Rules
- No IaC in this repo. No credentials in this repo. The marker must be emitted verbatim.
