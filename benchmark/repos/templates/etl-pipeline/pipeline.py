#!/usr/bin/env python3
"""A small ETL pipeline: extract records from object storage, transform (aggregate), load the result
into a key-value store. The system under test provisions the source bucket and the sink table and sets
CLOUDBENCH_INPUT_URI (s3://...) and CLOUDBENCH_TABLE; without them a bundled sample runs locally."""
import json
import os
import sys

_SAMPLE = [{"category": "a", "amount": 3}, {"category": "b", "amount": 5}, {"category": "a", "amount": 2}]


def extract() -> list:
    uri = os.environ.get("CLOUDBENCH_INPUT_URI")
    if uri and uri.startswith("s3://"):
        import boto3
        bucket, key = uri[5:].split("/", 1)
        body = boto3.client("s3").get_object(Bucket=bucket, Key=key)["Body"].read()
        return json.loads(body)
    return _SAMPLE


def transform(rows: list) -> dict:
    totals: dict = {}
    for r in rows:
        totals[r["category"]] = totals.get(r["category"], 0) + r["amount"]
    return totals


def load(totals: dict) -> None:
    table_name = os.environ.get("CLOUDBENCH_TABLE")
    if table_name:
        import boto3
        table = boto3.resource("dynamodb").Table(table_name)
        for category, total in totals.items():
            table.put_item(Item={"category": category, "total": total})


def main() -> int:
    totals = transform(extract())
    load(totals)
    print(f"CLOUDBENCH_ETL_OK aggregated {len(totals)} group(s): {json.dumps(totals)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
