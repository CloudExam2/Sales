"""CRUD tests on in-memory SQLite. Catalog validation is monkeypatched to a no-op."""

import pytest

pytestmark = pytest.mark.ephemeral

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def patch_catalog(monkeypatch):
    """Skip the real Catalog HTTP call in API tests."""
    async def _noop(_client_id, _product_ids):
        return None

    import routers.sales as sales_router

    monkeypatch.setattr(sales_router, "validate_catalog_entities", _noop)


def _sample_note(folio: str = "F-001") -> dict:
    return {
        "folio": folio,
        "client_id": 1,
        "fac_address_id": 10,
        "send_address_id": 20,
        "contents": [
            {"product_id": 100, "unit_price": "45.50", "quantity": 2},
            {"product_id": 101, "unit_price": "15.00", "quantity": 1},
        ],
    }


def test_create_sales_note():
    r = client.post("/sales/", json=_sample_note())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["folio"] == "F-001"
    assert body["client_id"] == 1
    assert body["fac_address_id"] == 10
    assert body["send_address_id"] == 20
    # 45.50 * 2 + 15.00 * 1 = 106.00
    assert float(body["total"]) == 106.00


def test_list_sales_notes():
    for folio in ("F-100", "F-101", "F-102"):
        r = client.post("/sales/", json=_sample_note(folio))
        assert r.status_code == 200, r.text

    listed = client.get("/sales/").json()
    assert {n["folio"] for n in listed} == {"F-100", "F-101", "F-102"}


def test_get_sales_note():
    created = client.post("/sales/", json=_sample_note("F-200")).json()
    nid = created["id"]

    fetched = client.get(f"/sales/{nid}")
    assert fetched.status_code == 200
    assert fetched.json()["folio"] == "F-200"


def test_get_nonexistent_sales_note():
    r = client.get("/sales/9999")
    assert r.status_code == 404


def test_delete_sales_note():
    nid = client.post("/sales/", json=_sample_note("F-300")).json()["id"]

    del_res = client.delete(f"/sales/{nid}")
    assert del_res.status_code == 200

    check = client.get(f"/sales/{nid}")
    assert check.status_code == 404


def test_create_with_missing_folio_is_422():
    bad = _sample_note()
    del bad["folio"]
    r = client.post("/sales/", json=bad)
    assert r.status_code == 422
