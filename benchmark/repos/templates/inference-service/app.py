#!/usr/bin/env python3
"""A small ML inference service: a Flask API that serves predictions from a model. The model is loaded
from object storage when CLOUDBENCH_MODEL_URI is set (the system under test provisions the bucket and
uploads the model); otherwise a tiny bundled fallback model is used so the app always runs."""
import json
import os

from flask import Flask, jsonify, request

app = Flask(__name__)

# A trivial linear model: score = w . features + b. In a real case this is loaded from S3.
_MODEL = {"weights": [0.5, 1.5], "bias": 0.1}


def _load_model() -> dict:
    uri = os.environ.get("CLOUDBENCH_MODEL_URI")
    if uri and uri.startswith("s3://"):
        import boto3
        bucket, key = uri[5:].split("/", 1)
        body = boto3.client("s3").get_object(Bucket=bucket, Key=key)["Body"].read()
        return json.loads(body)
    return _MODEL


@app.get("/health")
def health():
    return jsonify(status="ok", marker="CLOUDBENCH_MLAI_OK")


@app.post("/predict")
def predict():
    model = _load_model()
    feats = (request.get_json(silent=True) or {}).get("features", [])
    score = sum(w * x for w, x in zip(model["weights"], feats)) + model["bias"]
    return jsonify(prediction=score, marker="CLOUDBENCH_MLAI_OK")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
