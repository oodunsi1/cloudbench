"""Local proof: /health is 200 (no database), and /items works against a fake DB connection.

Run: ``python -m pytest`` from this directory (needs Flask; no PostgreSQL required).
"""
from __future__ import annotations

import app as appmod


def test_health_ok() -> None:
    client = appmod.create_app().test_client()
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


class FakeCursor:
    def __init__(self, store: list) -> None:
        self.store = store
        self._last = None
        self._rows: list = []

    def execute(self, sql, params=None):  # noqa: ANN001
        s = sql.lower()
        if "insert" in s:
            self.store.append(params[0])
            self._last = (len(self.store),)
        elif "select" in s:
            self._rows = [(i + 1, n) for i, n in enumerate(self.store)]

    def fetchone(self):
        return self._last

    def fetchall(self):
        return self._rows

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeConn:
    def __init__(self, store: list) -> None:
        self.store = store

    def cursor(self):
        return FakeCursor(self.store)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def close(self):
        pass


def test_items_round_trip() -> None:
    store: list = []
    client = appmod.create_app(connect=lambda: FakeConn(store)).test_client()

    created = client.post("/items", json={"name": "widget"})
    assert created.status_code == 201
    assert created.get_json()["name"] == "widget"

    listed = client.get("/items")
    assert listed.status_code == 200
    names = [i["name"] for i in listed.get_json()["items"]]
    assert "widget" in names


def test_items_requires_name() -> None:
    client = appmod.create_app(connect=lambda: None).test_client()
    r = client.post("/items", json={})
    assert r.status_code == 400
