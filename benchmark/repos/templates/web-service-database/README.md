# CloudBench AWS RDS API

A small **long-running web service** backed by a PostgreSQL database. It exposes a health check and a
tiny items API.

This repository is a **CloudBench benchmark case** (building block **B3** — compute plus a database).
It is the *application*, not the infrastructure: there is deliberately **no Terraform or other
infrastructure-as-code here**. Working out the cloud resources this app needs, creating them, running
the service, and proving it answers requests is the job of the repository-to-cloud system being
tested.

## What it does

| Method + path | Result |
|---|---|
| `GET /health` | `200 {"status": "ok"}` — liveness, needs no database |
| `POST /items` | `201 {"id", "name"}` — insert a row |
| `GET /items` | `200 {"items": [...]}` — list rows |

## Cloud resources it needs

| Resource | Why |
|---|---|
| A compute instance (e.g. EC2) | runs the web service |
| A managed PostgreSQL database (e.g. RDS) | stores the items |
| A security group | lets the instance reach the database and serve HTTP |
| An IAM role | the instance's identity |

No credentials live in this repo — the database URL is injected at runtime.

## How to run

```bash
export DATABASE_URL=postgresql://user:pass@host:5432/dbname   # provided by the provisioned database
./run.sh        # installs requirements, starts the service on PORT (default 8080)
```

`db/init.sql` documents the schema; the app also creates the table on demand, so a fresh database
works with no manual step.

## Success criteria (validation contract)

A run is successful when `GET /health` returns HTTP `200`.

## Local development

`/health` and the items round-trip are exercised with Flask's test client and a fake database
connection (no PostgreSQL needed):

```bash
python -m pip install -r requirements.txt pytest
python -m pytest
```
