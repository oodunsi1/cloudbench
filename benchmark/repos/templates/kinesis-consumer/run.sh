#!/usr/bin/env bash
set -euo pipefail
pip3 install -r requirements.txt -q
python3 consumer.py
