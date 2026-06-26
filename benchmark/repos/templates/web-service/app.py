#!/usr/bin/env python3
"""A small stateless HTTP service: a Flask API with a health check and an echo endpoint. No database
or external dependency — it just needs to be reachable. The system under test provisions compute and
exposes it."""
import os

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify(status="ok", marker="CLOUDBENCH_WEBAPI_OK")


@app.post("/echo")
def echo():
    return jsonify(echo=(request.get_json(silent=True) or {}), marker="CLOUDBENCH_WEBAPI_OK")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
