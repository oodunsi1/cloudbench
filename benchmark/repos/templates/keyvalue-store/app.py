#!/usr/bin/env python3
"""A small stateful worker: round-trip a record through a key-value store to prove persistence.
The system under test provisions the store (a DynamoDB table) and sets CLOUDBENCH_TABLE to its name."""
import os
import sys

import boto3


def main() -> int:
    table_name = os.environ.get("CLOUDBENCH_TABLE")
    if not table_name:
        print("Set CLOUDBENCH_TABLE to the provisioned DynamoDB table name", file=sys.stderr)
        return 2
    table = boto3.resource("dynamodb").Table(table_name)
    table.put_item(Item={"id": "cloudbench", "value": "hello-state"})
    got = table.get_item(Key={"id": "cloudbench"}).get("Item", {})
    if got.get("value") == "hello-state":
        print(f"CLOUDBENCH_STATEFUL_OK round-tripped a record through table {table_name}")
        return 0
    print(f"FAIL: read back {got!r}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
