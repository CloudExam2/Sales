"""Seed/clear helpers for live Sales + Catalog servers.

Sales validates against Catalog, so seeding a sales note needs:
  1. CATALOG_BASE_URL  → client + 2 addresses + products (or reuse existing)
  2. SALES_BASE_URL    → sales note; line unit_price is read from Catalog base_price

Set USE_EXISTING_CATALOG=true in Sales/.env to use the first client, two addresses,
and the first five products already on Catalog (e.g. after Catalog test_seed_data.py).
"""

import os
from pathlib import Path

import requests

DEFAULT_SALES_URL = "http://127.0.0.1:8000"
DEFAULT_CATALOG_URL = "http://127.0.0.1:8001"

DEMO_PRODUCTS = [
    {"name": "Industrial Copper Sulfate", "unit": "kg", "base_price": 45.50},
    {"name": "Potassium Permanganate", "unit": "kg", "base_price": 32.00},
    {"name": "ITESO Lab Flask", "unit": "unit", "base_price": 15.00},
    {"name": "Sodium Chloride", "unit": "kg", "base_price": 5.25},
    {"name": "Distilled Water", "unit": "L", "base_price": 8.00},
]

# One line per product; quantities for the demo sale total
DEMO_LINE_QUANTITIES = [2, 1, 3, 4, 2]


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


def _use_existing_catalog() -> bool:
    return os.getenv("USE_EXISTING_CATALOG", "").strip().lower() in ("1", "true", "yes")


def _check_reachable(label: str, url: str) -> None:
    try:
        r = requests.get(f"{url}/", timeout=15)
    except requests.ConnectionError as e:
        raise RuntimeError(
            f"{label} not reachable at {url}. Set {label}_BASE_URL in Sales/.env."
        ) from e
    if r.status_code != 200:
        raise RuntimeError(f"{label} not reachable at {url} (status {r.status_code})")


def _get_catalog_product(catalog_url: str, product_id: int) -> dict:
    r = requests.get(f"{catalog_url}/products/{product_id}", timeout=15)
    if r.status_code != 200:
        raise RuntimeError(
            f"Catalog GET /products/{product_id} failed: {r.status_code} {r.text}"
        )
    return r.json()


def _note_contents_from_catalog(
    catalog_url: str,
    product_ids: list[int],
    quantities: list[int],
) -> list[dict]:
    """Build sale lines using each product's current base_price from Catalog."""
    if len(product_ids) != len(quantities):
        raise ValueError("product_ids and quantities must have the same length")

    contents = []
    for pid, qty in zip(product_ids, quantities):
        prod = _get_catalog_product(catalog_url, pid)
        contents.append(
            {
                "product_id": pid,
                "unit_price": str(prod["base_price"]),
                "quantity": qty,
            }
        )
        print(
            f"  line product_id={pid} name={prod.get('name')} "
            f"unit_price={prod['base_price']} qty={qty}"
        )
    return contents


def _seed_catalog_for_sale(catalog_url: str) -> tuple[int, int, int, list[int]]:
    """Create one buyer + 2 addresses + 5 products. Returns ids."""
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
    for body in DEMO_PRODUCTS:
        r = requests.post(f"{catalog_url}/products/", json=body, timeout=15)
        if r.status_code != 200:
            raise RuntimeError(f"Catalog product create failed: {r.status_code} {r.text}")
        product_ids.append(r.json()["id"])

    return client_id, fac_id, env_id, product_ids


def _pick_existing_catalog_entities(catalog_url: str) -> tuple[int, int, int, list[int]]:
    """Use first client, one FAC + one ENV address, and first five products."""
    clients = requests.get(f"{catalog_url}/clients/", timeout=15).json()
    if not clients:
        raise RuntimeError("No clients on Catalog — run Catalog seed first or unset USE_EXISTING_CATALOG.")

    addresses = requests.get(f"{catalog_url}/addresses/", timeout=15).json()
    fac = next((a for a in addresses if a.get("address_type") == "FACTURACIÓN"), None)
    env = next((a for a in addresses if a.get("address_type") == "ENVÍO"), None)
    if not fac or not env:
        raise RuntimeError(
            "Need at least one FACTURACIÓN and one ENVÍO address on Catalog — run Catalog seed first."
        )

    products = requests.get(f"{catalog_url}/products/", timeout=15).json()
    if len(products) < 5:
        raise RuntimeError(
            f"Need at least 5 products on Catalog (found {len(products)}). "
            "Run Catalog test_seed_data.py or unset USE_EXISTING_CATALOG."
        )

    product_ids = [p["id"] for p in sorted(products, key=lambda p: p["id"])[:5]]
    client_id = clients[0]["id"]
    return client_id, fac["id"], env["id"], product_ids


def seed_sales(sales_url: str | None = None, catalog_url: str | None = None) -> dict:
    sales_url = (sales_url or get_sales_url()).rstrip("/")
    catalog_url = (catalog_url or get_catalog_url()).rstrip("/")

    _check_reachable("SALES", sales_url)
    _check_reachable("CATALOG", catalog_url)

    if _use_existing_catalog():
        print("Using existing Catalog data (USE_EXISTING_CATALOG=true)")
        client_id, fac_id, env_id, product_ids = _pick_existing_catalog_entities(catalog_url)
    else:
        print("Creating fresh Catalog demo buyer, addresses, and 5 products")
        client_id, fac_id, env_id, product_ids = _seed_catalog_for_sale(catalog_url)

    print("Building sale lines from Catalog base_price:")
    contents = _note_contents_from_catalog(
        catalog_url,
        product_ids,
        DEMO_LINE_QUANTITIES,
    )

    note_payload = {
        "folio": "F-SEED-001",
        "client_id": client_id,
        "fac_address_id": fac_id,
        "send_address_id": env_id,
        "contents": contents,
    }

    note_res = requests.post(f"{sales_url}/sales/", json=note_payload, timeout=30)
    if note_res.status_code != 200:
        raise RuntimeError(f"Sales note create failed: {note_res.status_code} {note_res.text}")
    note = note_res.json()

    print(f"Seeded at {sales_url} (via Catalog at {catalog_url})")
    print(f"  catalog client_id={client_id}, addresses=({fac_id}, {env_id})")
    print(f"  catalog product_ids={product_ids}")
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
