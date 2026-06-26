# CloudBench — AWS cache-backed service (B3, work-kind: service)

A cache-backed HTTP service (`app.py`, Flask + Redis): `POST /set` and `GET /get/<key>` store and read
through a Redis cache (ElastiCache); `GET /health` returns `CLOUDBENCH_CACHE_OK`. No IaC in this repo —
provisioning compute + the cache is the system under test's job (set `CLOUDBENCH_REDIS_HOST`).

## How "it works" is proven
`GET /health` returns 200 with the marker, and set→get round-trips a value through the cache.

## Rules
- No IaC in this repo. No credentials in this repo. The marker must be served verbatim.
