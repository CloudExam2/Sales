"""Seed/clear helpers for live Sales + Catalog servers.

Sales validates against Catalog, so seeding a sales note needs:
  1. CATALOG_BASE_URL  → client + 2 addresses + products (or reuse existing)
  2. SALES_BASE_URL    → sales note; line unit_price is read from Catalog base_price

Set USE_EXISTING_CATALOG=true in Sales/.env to use the first client, two addresses,
and the first five products already on Catalog (e.g. after Catalog test_seed_data.py).
"""

import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


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


def _delete_all_catalog(catalog_url: str, path: str) -> int:
    items = requests.get(f"{catalog_url}{path}", timeout=30).json()
    deleted = 0
    for row in items:
        r = requests.delete(f"{catalog_url}{path}{row['id']}", timeout=30)
        if r.status_code == 200:
            deleted += 1
    return deleted


def clear_catalog(catalog_url: str | None = None) -> None:
    """Delete all Catalog clients, products, and addresses."""
    catalog_url = (catalog_url or get_catalog_url()).rstrip("/")
    _check_reachable("CATALOG", catalog_url)

    deleted_clients = _delete_all_catalog(catalog_url, "/clients/")
    deleted_products = _delete_all_catalog(catalog_url, "/products/")
    deleted_addresses = _delete_all_catalog(catalog_url, "/addresses/")

    print(f"Cleared Catalog at {catalog_url}")
    print(f"  deleted clients:   {deleted_clients}")
    print(f"  deleted products:  {deleted_products}")
    print(f"  deleted addresses: {deleted_addresses}")


def _setup_catalog_for_load(
    catalog_url: str,
    num_clients: int,
    num_products: int,
) -> tuple[list[dict], list[int]]:
    """Create clients (with FAC/ENV addresses) and products. Returns buyers + product ids."""
    buyers: list[dict] = []

    for i in range(num_clients):
        c_res = requests.post(
            f"{catalog_url}/clients/",
            json={
                "rfc": f"LDCL{i:08d}",
                "razon_social": f"Load Buyer {i}",
                "email": f"loadbuyer{i}@load.test",
            },
            timeout=30,
        )
        if c_res.status_code != 200:
            raise RuntimeError(f"Load client {i} failed: {c_res.status_code} {c_res.text}")
        client_id = c_res.json()["id"]

        fac_res = requests.post(
            f"{catalog_url}/addresses/",
            json={
                "domicilio": f"Load Fac {i}",
                "address_type": "FACTURACIÓN",
            },
            timeout=30,
        )
        env_res = requests.post(
            f"{catalog_url}/addresses/",
            json={
                "domicilio": f"Load Env {i}",
                "address_type": "ENVÍO",
            },
            timeout=30,
        )
        for r in (fac_res, env_res):
            if r.status_code != 200:
                raise RuntimeError(f"Load address failed: {r.status_code} {r.text}")

        buyers.append(
            {
                "client_id": client_id,
                "fac_address_id": fac_res.json()["id"],
                "send_address_id": env_res.json()["id"],
            }
        )

    product_ids: list[int] = []
    for i in range(num_products):
        p_res = requests.post(
            f"{catalog_url}/products/",
            json={
                "name": f"Load product {i}",
                "unit": "kg",
                "base_price": 10.0 + (i % 50),
            },
            timeout=30,
        )
        if p_res.status_code != 200:
            raise RuntimeError(f"Load product {i} failed: {p_res.status_code} {p_res.text}")
        product_ids.append(p_res.json()["id"])

    return buyers, product_ids


def load_test_then_clear(
    sales_url: str | None = None,
    catalog_url: str | None = None,
) -> None:
    """
    Bulk Catalog data + many Sales notes (each POST validates client + products in Catalog),
    optional parallel GET/POST stress, then wipe Sales and Catalog.

    Tune with env: LOAD_CLIENTS, LOAD_PRODUCTS, LOAD_SALES_NOTES, LOAD_LINES_PER_SALE,
    LOAD_HTTP_ROUNDS, LOAD_WORKERS.
    """
    sales_url = (sales_url or get_sales_url()).rstrip("/")
    catalog_url = (catalog_url or get_catalog_url()).rstrip("/")

    num_clients = _env_int("LOAD_CLIENTS", 15)
    num_products = _env_int("LOAD_PRODUCTS", 40)
    num_sales = _env_int("LOAD_SALES_NOTES", 80)
    lines_per_sale = _env_int("LOAD_LINES_PER_SALE", 3)
    http_rounds = _env_int("LOAD_HTTP_ROUNDS", 100)
    workers = _env_int("LOAD_WORKERS", 12)

    _check_reachable("SALES", sales_url)
    _check_reachable("CATALOG", catalog_url)

    print(f"Load test Sales @ {sales_url} (Catalog @ {catalog_url})")
    print(
        f"  clients={num_clients}, products={num_products}, sales_notes={num_sales}, "
        f"lines/sale={lines_per_sale}, http_rounds={http_rounds}, workers={workers}"
    )
    print("  Watch CloudWatch dashboard Exam2-EC2-Overview (CPU on both EC2).")

    print("  Phase 1 — seed Catalog buyers + products...")
    buyers, product_ids = _setup_catalog_for_load(catalog_url, num_clients, num_products)
    print(f"    {len(buyers)} buyers, {len(product_ids)} products")

    # Cache prices once (Sales still re-validates against Catalog on each POST).
    product_prices = {
        pid: str(_get_catalog_product(catalog_url, pid)["base_price"]) for pid in product_ids
    }

    def _create_one_sale(i: int) -> None:
        buyer = buyers[i % len(buyers)]
        line_pids = random.sample(product_ids, min(lines_per_sale, len(product_ids)))
        contents = [
            {
                "product_id": pid,
                "unit_price": product_prices[pid],
                "quantity": 1 + (i % 4),
            }
            for pid in line_pids
        ]
        payload = {
            "folio": f"F-LOAD-{i:05d}",
            "client_id": buyer["client_id"],
            "fac_address_id": buyer["fac_address_id"],
            "send_address_id": buyer["send_address_id"],
            "contents": contents,
        }
        r = requests.post(f"{sales_url}/sales/", json=payload, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"Sale {i} failed: {r.status_code} {r.text}")

    print(f"  Phase 2 — create {num_sales} sales notes (Catalog validation per note)...")
    created = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_create_one_sale, i) for i in range(num_sales)]
        for fut in as_completed(futures):
            fut.result()
            created += 1
            if created % 20 == 0:
                print(f"    ... {created}/{num_sales} sales")

    print(f"  Phase 3 — HTTP stress ({http_rounds} rounds, {workers} workers)...")

    def _stress_round(_: int) -> None:
        requests.get(f"{sales_url}/sales/", timeout=60)
        requests.get(f"{sales_url}/", timeout=60)
        requests.get(f"{catalog_url}/products/", timeout=60)
        requests.get(f"{catalog_url}/clients/", timeout=60)

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_stress_round, n) for n in range(http_rounds)]
        for fut in as_completed(futures):
            fut.result()
            done += 1
            if done % 25 == 0:
                print(f"    ... {done}/{http_rounds} rounds")

    print("  Phase 4 — clearing Sales, then Catalog...")
    clear_sales(sales_url)
    clear_catalog(catalog_url)
    print("  load test finished (Sales + Catalog cleared).")
