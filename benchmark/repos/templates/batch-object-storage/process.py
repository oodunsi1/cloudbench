#!/usr/bin/env python3
"""CloudBench AWS S3 Batch — read a text object from S3, count words, write the result back.

This is a *benchmark application*. It declares the cloud resources it NEEDS — an S3 bucket it can
read from and write to, running on a compute instance whose IAM role grants ``s3:GetObject`` and
``s3:PutObject`` — but it contains NO infrastructure-as-code. Provisioning those resources is the
job of the repository-to-cloud system under test.

Run-to-completion batch job:
  input  s3://<bucket>/input.txt
  output s3://<bucket>/output/result.json   (word counts)
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

import boto3
import yaml

CONFIG_PATH = Path(__file__).resolve().parent / "config.yml"


def count_words(text: str) -> dict[str, int]:
    """Return a ``word -> count`` mapping. Tokens are split on whitespace."""
    return dict(Counter(text.split()))


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Load ``config.yml`` and apply environment-variable overrides.

    The bucket name is supplied at runtime by the provisioned infrastructure (env var
    ``CLOUDBENCH_BUCKET``), never hard-coded here.
    """
    cfg: dict = {}
    if path.exists():
        cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cfg["bucket"] = os.environ.get("CLOUDBENCH_BUCKET", cfg.get("bucket") or "")
    cfg["input_key"] = os.environ.get("CLOUDBENCH_INPUT_KEY", cfg.get("input_key") or "input.txt")
    cfg["output_key"] = os.environ.get(
        "CLOUDBENCH_OUTPUT_KEY", cfg.get("output_key") or "output/result.json"
    )
    cfg["region"] = (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or cfg.get("region")
        or "us-east-1"
    )
    return cfg


def process(s3, bucket: str, input_key: str, output_key: str) -> str:
    """Read ``input_key`` from ``bucket``, count words, write the result JSON to ``output_key``.

    Returns the ``s3://`` URI of the written output object.
    """
    if not bucket:
        raise ValueError("No bucket configured. Set CLOUDBENCH_BUCKET or config.yml 'bucket'.")
    obj = s3.get_object(Bucket=bucket, Key=input_key)
    text = obj["Body"].read().decode("utf-8")
    counts = count_words(text)
    payload = {"word_counts": counts, "total_words": sum(counts.values())}
    body = json.dumps(payload, indent=2).encode("utf-8")
    s3.put_object(Bucket=bucket, Key=output_key, Body=body, ContentType="application/json")
    return f"s3://{bucket}/{output_key}"


def main(argv: list[str] | None = None) -> int:
    cfg = load_config()
    s3 = boto3.client("s3", region_name=cfg["region"])
    uri = process(s3, cfg["bucket"], cfg["input_key"], cfg["output_key"])
    print(f"Wrote word counts to {uri}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
