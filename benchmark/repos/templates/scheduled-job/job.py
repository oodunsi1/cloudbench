#!/usr/bin/env python3
"""A small recurring job: append a heartbeat line with a marker and a UTC timestamp to the output
file. The system under test runs this on a schedule (cron / systemd timer / EventBridge)."""
import datetime
import os
import pathlib

OUT = pathlib.Path(os.environ.get("CLOUDBENCH_OUTPUT", "output/heartbeat.log"))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with OUT.open("a", encoding="utf-8") as fh:
        fh.write(f"CLOUDBENCH_CRON_OK {stamp}\n")
    print(f"CLOUDBENCH_CRON_OK wrote heartbeat at {stamp} -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
