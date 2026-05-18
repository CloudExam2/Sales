"""Seed/clear helpers for live Sales + Catalog servers.

Sales validates against Catalog, so seeding a sales note needs:
  1. CATALOG_BASE_URL  → POST a client + 2 addresses + a few products
  2. SALES_BASE_URL    → POST a sales note referencing those ids
"""

import os
from pathlib import Path

import requests

DEFAULT_SALES_URL = "http://127.0.0.1:8000"
DEFAULT_CATALOG_URL = "http://127.0.0.1:8001"


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    sales_root = Path(__file__).resolve().parents[1]
    load_dotenv(sales_root / ".env")


_load_dotenv()


def get_sales_url() -> str:
    return os.getenv("SALES_BASE_URL", DEFAULT_SALES_URL).rstrip("/")


def get_catalog_url() -> str:
    return os.getenv("CATALOG_BASE_URL", DEFAULT_CATALOG_URL).rstrip("/")


def _check_reachable(label: str, url: str) -> None:
    try:
        r = requests.get(f"{url}/", timeout=15)
    except requests.ConnectionError as e:
        raise RuntimeError(
            f"{label} not reachable at {url}. Set {label}_BASE_URL in Sales/.env."
        ) from e
    if r.status_code != 200:
        raise RuntimeError(f"{label} not reachable at {url} (status {r.status_code})")


def _seed_catalog_for_sale(catalog_url: str) -> tuple[int, int, int, list[int]]:
    """Create one buyer + 2 addresses + 3 products in Catalog. Returns ids."""
    client_res = requests.post(
        f"{catalog_url}/clients/",
        json={
            "rfc": "SALEBUYR1234",
            "razon_social": "Sales Demo Buyer",
            "email": "sale@buyer.test",
        },
        timeout=15,
    )
    if client_res.status_code != 200:
        raise RuntimeError(f"Catalog client create failed: {client_res.status_code} {client_res.text}")
    client_id = client_res.json()["id"]

    fac_res = requests.post(
        f"{catalog_url}/addresses/",
        json={"domicilio": "Av. Vallarta 100", "address_type": "FACTURACIÓN"},
        timeout=15,
    )
    env_res = requests.post(
        f"{catalog_url}/addresses/",
        json={"domicilio": "Av. Patria 200", "address_type": "ENVÍO"},
        timeout=15,
    )
    for r in (fac_res, env_res):
        if r.status_code != 200:
            raise RuntimeError(f"Catalog address create failed: {r.status_code} {r.text}")
    fac_id = fac_res.json()["id"]
    env_id = env_res.json()["id"]

    product_ids: list[int] = []
    for body in [
        {"name": "Industrial Copper Sulfate", "unit": "kg", "base_price": 45.50},
        {"name": "Potassium Permanganate", "unit": "kg", "base_price": 32.00},
        {"name": "ITESO Lab Flask", "unit": "unit", "base_price": 15.00},
    ]:
        r = requests.post(f"{catalog_url}/products/", json=body, timeout=15)
        if r.status_code != 200:
            raise RuntimeError(f"Catalog product create failed: {r.status_code} {r.text}")
        product_ids.append(r.json()["id"])

    return client_id, fac_id, env_id, product_ids


def seed_sales(sales_url: str | None = None, catalog_url: str | None = None) -> dict:
    sales_url = (sales_url or get_sales_url()).rstrip("/")
    catalog_url = (catalog_url or get_catalog_url()).rstrip("/")

    _check_reachable("SALES", sales_url)
    _check_reachable("CATALOG", catalog_url)

    client_id, fac_id, env_id, product_ids = _seed_catalog_for_sale(catalog_url)

    note_payload = {
        "folio": "F-SEED-001",
        "client_id": client_id,
        "fac_address_id": fac_id,
        "send_address_id": env_id,
        "contents": [
            {"product_id": product_ids[0], "unit_price": "45.50", "quantity": 2},
            {"product_id": product_ids[1], "unit_price": "32.00", "quantity": 1},
            {"product_id": product_ids[2], "unit_price": "15.00", "quantity": 5},
        ],
    }

    note_res = requests.post(f"{sales_url}/sales/", json=note_payload, timeout=30)
    if note_res.status_code != 200:
        raise RuntimeError(f"Sales note create failed: {note_res.status_code} {note_res.text}")
    note = note_res.json()

    print(f"Seeded at {sales_url} (via Catalog at {catalog_url})")
    print(f"  catalog client_id={client_id}, addresses=({fac_id}, {env_id})")
    print(f"  catalog products={product_ids}")
    print(f"  sales note id={note['id']}, folio={note['folio']}, total={note['total']}")

    return {
        "catalog_client_id": client_id,
        "catalog_address_ids": (fac_id, env_id),
        "catalog_product_ids": product_ids,
        "sales_note_id": note["id"],
    }


def clear_sales(sales_url: str | None = None) -> None:
    """Delete every sales note. Catalog data is left alone."""
    sales_url = (sales_url or get_sales_url()).rstrip("/")
    _check_reachable("SALES", sales_url)

    notes = requests.get(f"{sales_url}/sales/", timeout=15).json()
    deleted = 0
    for note in notes:
        r = requests.delete(f"{sales_url}/sales/{note['id']}", timeout=15)
        if r.status_code == 200:
            deleted += 1

    remaining = requests.get(f"{sales_url}/sales/", timeout=15).json()
    print(f"Cleared at {sales_url}")
    print(f"  deleted notes: {deleted}")
    print(f"  notes remaining: {len(remaining)}")
