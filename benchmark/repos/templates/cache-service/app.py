#!/usr/bin/env python3
"""A cache-backed HTTP service: a Flask API that stores and reads values through a Redis cache
(ElastiCache). The system under test provisions compute + the cache and sets CLOUDBENCH_REDIS_HOST;
without it an in-memory fallback keeps the app runnable for local smoke."""
import os

from flask import Flask, jsonify, request

app = Flask(__name__)
_fallback: dict = {}


def _client():
    host = os.environ.get("CLOUDBENCH_REDIS_HOST")
    if not host:
        return None
    import redis
    return redis.Redis(host=host, port=int(os.environ.get("CLOUDBENCH_REDIS_PORT", 6379)), decode_responses=True)


@app.get("/health")
def health():
    return jsonify(status="ok", marker="CLOUDBENCH_CACHE_OK")


@app.post("/set")
def set_value():
    body = request.get_json(silent=True) or {}
    k, v = body.get("key", "k"), body.get("value", "v")
    c = _client()
    (c.set(k, v) if c else _fallback.__setitem__(k, v))
    return jsonify(ok=True, marker="CLOUDBENCH_CACHE_OK")


@app.get("/get/<key>")
def get_value(key):
    c = _client()
    val = c.get(key) if c else _fallback.get(key)
    return jsonify(key=key, value=val, marker="CLOUDBENCH_CACHE_OK")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
