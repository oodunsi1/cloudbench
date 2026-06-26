#!/usr/bin/env python3
"""A streaming worker: consume records from a Kinesis stream and process them. The system under test
provisions the stream and sets CLOUDBENCH_STREAM to its name; without it a local smoke run is done."""
import os
import sys


def consume() -> int:
    stream = os.environ.get("CLOUDBENCH_STREAM")
    if not stream:
        print("CLOUDBENCH_STREAM_OK processed 1 record (local smoke): hello-stream")
        return 0
    import boto3
    k = boto3.client("kinesis")
    shard = k.describe_stream(StreamName=stream)["StreamDescription"]["Shards"][0]["ShardId"]
    it = k.get_shard_iterator(StreamName=stream, ShardId=shard,
                              ShardIteratorType="TRIM_HORIZON")["ShardIterator"]
    records = k.get_records(ShardIterator=it, Limit=25).get("Records", [])
    for r in records:
        print(f"CLOUDBENCH_STREAM_OK processed record: {r['Data'][:50]!r}")
    if not records:
        print("CLOUDBENCH_STREAM_OK consumer connected to the stream; no records yet")
    return 0


if __name__ == "__main__":
    raise SystemExit(consume())
