#!/usr/bin/env bash
# CloudBench AWS S3 Batch — entry point.
#
# Expects:
#   * Python 3.10+
#   * an S3 bucket name in the CLOUDBENCH_BUCKET environment variable
#   * AWS credentials available via the instance's IAM role (no keys live in this repo)
set -euo pipefail

cd "$(dirname "$0")"
python3 -m pip install --quiet --requirement requirements.txt
exec python3 process.py
