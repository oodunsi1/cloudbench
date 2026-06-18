#!/usr/bin/env python3
"""CloudBench AWS RDS API — a small long-running web service backed by PostgreSQL.

This is a *benchmark application*. It declares the cloud resources it NEEDS — a compute instance and
a managed PostgreSQL database, reachable through a security group — but contains NO
infrastructure-as-code. Provisioning those is the job of the repository-to-cloud system under test.

Endpoints:
  GET  /health  -> 200 {"status": "ok"}        (liveness; no database needed)
  POST /items   -> 201 {"id", "name"}          (insert a row)
  GET  /items   -> 200 {"items": [...]}        (list rows)

The database connection string is injected at runtime via DATABASE_URL — never stored in this repo.
"""
from __future__ import annotations

import os

from flask import Flask, jsonify, request


def _connect():
    """Connect to PostgreSQL using DATABASE_URL. psycopg2 is imported lazily so the module can be
    imported (and /health tested) without the driver or a live database present."""
    import psycopg2

    return psycopg2.connect(os.environ["DATABASE_URL"])


def create_app(connect=_connect) -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    @app.post("/items")
    def add_item():
        name = (request.get_json(silent=True) or {}).get("name")
        if not name:
            return jsonify(error="name required"), 400
        conn = connect()
        try:
            with conn, conn.cursor() as cur:
                cur.execute("CREATE TABLE IF NOT EXISTS items (id SERIAL PRIMARY KEY, name TEXT)")
                cur.execute("INSERT INTO items (name) VALUES (%s) RETURNING id", (name,))
                new_id = cur.fetchone()[0]
        finally:
            conn.close()
        return jsonify(id=new_id, name=name), 201

    @app.get("/items")
    def list_items():
        conn = connect()
        try:
            with conn, conn.cursor() as cur:
                cur.execute("CREATE TABLE IF NOT EXISTS items (id SERIAL PRIMARY KEY, name TEXT)")
                cur.execute("SELECT id, name FROM items ORDER BY id")
                rows = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]
        finally:
            conn.close()
        return jsonify(items=rows), 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
