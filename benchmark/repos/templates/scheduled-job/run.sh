#!/usr/bin/env bash
# Run the job once. The system under test schedules this to run recurringly (cron/systemd/EventBridge);
# a single invocation here is what each scheduled tick executes.
set -euo pipefail
python3 job.py
