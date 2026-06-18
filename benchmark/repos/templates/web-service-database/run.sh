#!/usr/bin/env bash
# CloudBench AWS RDS API — entry point.
#
# Expects:
#   * Python 3.10+
#   * a PostgreSQL connection string in the DATABASE_URL environment variable
#   * the database reachable from this instance (security group / networking provisioned for you)
set -euo pipefail

cd "$(dirname "$0")"
python3 -m pip install --quiet --requirement requirements.txt
exec python3 app.py
