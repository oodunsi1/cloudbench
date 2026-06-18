"""Local proof that the batch app runs — uses an in-memory fake S3 (no AWS, no moto).

Run: ``python -m pytest`` from this directory.
"""
from __future__ import annotations

import io
import json

import process


class FakeS3:
    """Minimal in-memory stand-in for a boto3 S3 client (get_object / put_object)."""

    def __init__(self) -> None:
        self.store: dict[tuple[str, str], bytes] = {}

    def get_object(self, Bucket, Key):  # noqa: N803 — match boto3 kwarg names
        return {"Body": io.BytesIO(self.store[(Bucket, Key)])}

    def put_object(self, Bucket, Key, Body, **kwargs):  # noqa: N803
        self.store[(Bucket, Key)] = Body


def test_count_words() -> None:
    assert process.count_words("a a b") == {"a": 2, "b": 1}


def test_process_round_trip() -> None:
    s3 = FakeS3()
    s3.store[("bench-bucket", "input.txt")] = b"the cat sat on the mat the cat"
    uri = process.process(s3, "bench-bucket", "input.txt", "output/result.json")
    assert uri == "s3://bench-bucket/output/result.json"
    written = json.loads(s3.store[("bench-bucket", "output/result.json")])
    assert written["word_counts"]["the"] == 3
    assert written["word_counts"]["cat"] == 2
    assert written["total_words"] == 8


def test_main_with_monkeypatched_boto3(monkeypatch, capsys) -> None:
    s3 = FakeS3()
    s3.store[("bench-bucket", "input.txt")] = b"hello hello world"
    monkeypatch.setattr(process.boto3, "client", lambda *a, **k: s3)
    monkeypatch.setenv("CLOUDBENCH_BUCKET", "bench-bucket")
    rc = process.main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "s3://bench-bucket/output/result.json" in out
