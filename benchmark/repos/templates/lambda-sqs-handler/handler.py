#!/usr/bin/env python3
"""An event-driven worker: an AWS Lambda handler triggered by SQS. For each message it does a tiny
unit of work and emits a marker. The system under test packages this as a Lambda and wires an SQS
trigger to it; no infrastructure-as-code lives in this repo."""
import json


def handler(event, context=None):
    records = (event or {}).get("Records", [])
    processed = []
    for r in records:
        body = r.get("body", "")
        processed.append(body)
        print(f"CLOUDBENCH_EVENT_OK processed message: {body}")
    return {"statusCode": 200, "processed": len(processed),
            "marker": "CLOUDBENCH_EVENT_OK", "bodies": processed}


if __name__ == "__main__":
    # Local smoke test with a synthetic SQS event.
    print(json.dumps(handler({"Records": [{"body": "hello-event"}]})))
