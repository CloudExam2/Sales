"""Smoke tests: quick health checks — 'smoke' = shallow sanity test (no OpenAI involved)."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.ephemeral


def test_health_endpoint():
    from main import app

    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "healthy"
    assert body.get("service") == "sales"


def test_openapi_available():
    from main import app

    client = TestClient(app)
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert spec.get("openapi")
    assert "paths" in spec
    assert "/sales/" in spec["paths"]
