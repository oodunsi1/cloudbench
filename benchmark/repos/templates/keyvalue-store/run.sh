#!/usr/bin/env bash
# Install deps and run the stateful worker. The system under test provisions the key-value store and
# sets CLOUDBENCH_TABLE; the instance's IAM role grants DynamoDB access.
set -euo pipefail
pip3 install -r requirements.txt -q
python3 app.py
