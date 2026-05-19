"""Seed/clear helpers for live Sales + Catalog servers.

Sales validates against Catalog, so seeding a sales note needs:
  1. CATALOG_BASE_URL  → client + 2 addresses + products (or reuse existing)
  2. SALES_BASE_URL    → sales note (POST lines: product_id + quantity; Sales reads Catalog prices)

Set USE_EXISTING_CATALOG=true in Sales/.env to use the first client, two addresses,
and the first five products already on Catalog (e.g. after Catalog test_seed_data.py).
"""

import os
import random
import time
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
    """Build POST /sales/ lines (product_id + quantity). Logs Catalog prices for visibility."""
    if len(product_ids) != len(quantities):
        raise ValueError("product_ids and quantities must have the same length")

    contents = []
    for pid, qty in zip(product_ids, quantities):
        prod = _get_catalog_product(catalog_url, pid)
        contents.append({"product_id": pid, "quantity": qty})
        print(
            f"  line product_id={pid} name={prod.get('name')} "
            f"catalog_base_price={prod['base_price']} qty={qty}"
        )
    return contents


_SALE_BUYER_RFC = "SALEBUYR1234"


def _catalog_client_id_by_rfc(catalog_url: str, rfc: str) -> int | None:
    clients = requests.get(f"{catalog_url}/clients/", timeout=15)
    if clients.status_code != 200:
        return None
    for row in clients.json():
        if row.get("rfc") == rfc:
            return row["id"]
    return None


def _ensure_sale_demo_client(catalog_url: str) -> int:
    """Create SALEBUYR1234 buyer or reuse if a previous seed run left it on Catalog."""
    payload = {
        "rfc": _SALE_BUYER_RFC,
        "razon_social": "Sales Demo Buyer",
        "email": "sale@buyer.test",
    }
    client_res = requests.post(f"{catalog_url}/clients/", json=payload, timeout=15)
    if client_res.status_code == 200:
        return client_res.json()["id"]
    if client_res.status_code == 409:
        existing = _catalog_client_id_by_rfc(catalog_url, _SALE_BUYER_RFC)
        if existing is not None:
            return existing
    raise RuntimeError(f"Catalog client create failed: {client_res.status_code} {client_res.text}")


def _seed_catalog_for_sale(catalog_url: str) -> tuple[int, int, int, list[int]]:
    """Create one buyer + 2 addresses + 5 products. Returns ids."""
    client_id = _ensure_sale_demo_client(catalog_url)

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


def create_one_sale(
    sales_url: str | None = None,
    catalog_url: str | None = None,
    *,
    folio: str | None = None,
) -> dict:
    """
    Create a single sales note (Catalog seed + one POST /sales/).
    Used by test_sale_sqs_notification.py to trigger SQS → Lambda → email.
    """
    sales_url = (sales_url or get_sales_url()).rstrip("/")
    catalog_url = (catalog_url or get_catalog_url()).rstrip("/")
    _check_reachable("SALES", sales_url)
    _check_reachable("CATALOG", catalog_url)

    if _use_existing_catalog():
        client_id, fac_id, env_id, product_ids = _pick_existing_catalog_entities(catalog_url)
    else:
        client_id, fac_id, env_id, product_ids = _seed_catalog_for_sale(catalog_url)

    if folio is None:
        folio = f"F-NOTIFY-{int(time.time())}"

    contents = _note_contents_from_catalog(
        catalog_url,
        product_ids[:1],
        [1],
    )
    payload = {
        "folio": folio,
        "client_id": client_id,
        "fac_address_id": fac_id,
        "send_address_id": env_id,
        "contents": contents,
    }
    res = requests.post(f"{sales_url}/sales/", json=payload, timeout=60)
    if res.status_code != 200:
        raise RuntimeError(f"POST /sales/ failed: {res.status_code} {res.text}")
    return res.json()


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
    print("  If SQS is configured on Sales EC2, check email for sale notification (SQS → Lambda → SNS).")

    return {
        "catalog_client_id": client_id,
        "catalog_address_ids": (fac_id, env_id),
        "catalog_product_ids": product_ids,
        "sales_note_id": note["id"],
    }


def emit_sales_http_errors(
    sales_url: str | None = None,
    catalog_url: str | None = None,
    *,
    buyer: dict | None = None,
    product_ids: list[int] | None = None,
    reps: int | None = None,
) -> None:
    """Send 404 / 422 / 400 / 500 traffic for CloudWatch HTTP % widgets."""
    sales_url = (sales_url or get_sales_url()).rstrip("/")
    catalog_url = (catalog_url or get_catalog_url()).rstrip("/")
    reps = reps if reps is not None else _env_int("LOAD_ERROR_REPS", 40)
    print(f"  HTTP error traffic @ {sales_url} ({reps} rounds)...")

    bad_sale = {
        "folio": "ERR-BAD-CATALOG",
        "client_id": 999999999,
        "fac_address_id": 888888888,
        "send_address_id": 777777777,
        "contents": [
            {"product_id": 666666666, "unit_price": "10.00", "quantity": 1},
        ],
    }

    for _ in range(reps):
        requests.get(f"{sales_url}/sales/999999999", timeout=15)
        requests.get(f"{sales_url}/note-contents/999999999", timeout=15)
        requests.post(f"{sales_url}/sales/", json={}, timeout=15)
        requests.post(f"{sales_url}/sales/", json=bad_sale, timeout=15)

    if buyer and product_ids:
        dup_folio = f"DUP-LOAD-{int(time.time()) % 100000}"
        ok_payload = {
            "folio": dup_folio,
            "client_id": buyer["client_id"],
            "fac_address_id": buyer["fac_address_id"],
            "send_address_id": buyer["send_address_id"],
            "contents": [
                {
                    "product_id": product_ids[0],
                    "unit_price": "10.00",
                    "quantity": 1,
                }
            ],
        }
        first = requests.post(f"{sales_url}/sales/", json=ok_payload, timeout=30)
        if first.status_code == 200:
            for _ in range(min(reps, 15)):
                requests.post(f"{sales_url}/sales/", json=ok_payload, timeout=15)
        else:
            print(f"    (skip duplicate-folio 500 test: first sale returned {first.status_code})")

    if catalog_url:
        cat_rounds = min(reps, 20)
        for _ in range(cat_rounds):
            requests.get(f"{catalog_url}/clients/999999999", timeout=15)
            requests.get(f"{catalog_url}/products/888888888", timeout=15)
            requests.post(f"{catalog_url}/clients/", json={"rfc": "BAD"}, timeout=15)
            requests.put(
                f"{catalog_url}/clients/999999999",
                json={"razon_social": "ghost"},
                timeout=15,
            )


def clear_sales(
    sales_url: str | None = None,
    catalog_url: str | None = None,
    *,
    emit_errors: bool = True,
) -> None:
    """Delete every note line and sales note (orphan lines first for SQLite safety)."""
    sales_url = (sales_url or get_sales_url()).rstrip("/")
    catalog_url = (catalog_url or get_catalog_url()).rstrip("/")
    _check_reachable("SALES", sales_url)
    if emit_errors:
        emit_sales_http_errors(sales_url, catalog_url)

    deleted_lines = 0
    for row in requests.get(f"{sales_url}/note-contents/", timeout=15).json():
        r = requests.delete(f"{sales_url}/note-contents/{row['id']}", timeout=15)
        if r.status_code == 200:
            deleted_lines += 1

    deleted_notes = 0
    for note in requests.get(f"{sales_url}/sales/", timeout=15).json():
        r = requests.delete(f"{sales_url}/sales/{note['id']}", timeout=15)
        if r.status_code == 200:
            deleted_notes += 1

    lines_left = requests.get(f"{sales_url}/note-contents/", timeout=15).json()
    notes_left = requests.get(f"{sales_url}/sales/", timeout=15).json()
    print(f"Cleared at {sales_url}")
    print(f"  deleted note lines: {deleted_lines}")
    print(f"  deleted notes:      {deleted_notes}")
    print(f"  lines remaining:    {len(lines_left)}")
    print(f"  notes remaining:    {len(notes_left)}")


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


def _load_rfc(index: int, run_tag: int) -> str:
    """12–13 char RFC unique per run (avoids duplicate-key 500 after a failed load test)."""
    # LD + 6-digit index + 4-digit run tag = 12 chars (schema allows 12–13)
    return f"LD{index:06d}{run_tag:04d}"


def _setup_catalog_for_load(
    catalog_url: str,
    num_clients: int,
    num_products: int,
    run_tag: int,
) -> tuple[list[dict], list[int]]:
    """Create clients (with FAC/ENV addresses) and products. Returns buyers + product ids."""
    buyers: list[dict] = []

    for i in range(num_clients):
        c_res = requests.post(
            f"{catalog_url}/clients/",
            json={
                "rfc": _load_rfc(i, run_tag),
                "razon_social": f"Load Buyer {i}",
                "email": f"loadbuyer{i}@load.test",
            },
            timeout=30,
        )
        if c_res.status_code != 200:
            raise RuntimeError(
                f"Load client {i} failed: {c_res.status_code} {c_res.text!r}. "
                "Try: python tests/test_clear_data.py (Catalog) or lower LOAD_CLIENTS in .env."
            )
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

    run_tag = int(time.time()) % 10000
    print("  Clearing existing Sales + Catalog data before load...")
    clear_sales(sales_url)
    clear_catalog(catalog_url)

    print(f"Load test Sales @ {sales_url} (Catalog @ {catalog_url})")
    print(
        f"  clients={num_clients}, products={num_products}, sales_notes={num_sales}, "
        f"lines/sale={lines_per_sale}, http_rounds={http_rounds}, workers={workers}"
    )
    print("  Watch CloudWatch dashboard Exam2-EC2-Overview (CPU on both EC2).")

    print("  Phase 1 — seed Catalog buyers + products...")
    buyers, product_ids = _setup_catalog_for_load(catalog_url, num_clients, num_products, run_tag)
    print(f"    {len(buyers)} buyers, {len(product_ids)} products")

    def _create_one_sale(i: int) -> None:
        buyer = buyers[i % len(buyers)]
        line_pids = random.sample(product_ids, min(lines_per_sale, len(product_ids)))
        contents = [
            {"product_id": pid, "quantity": 1 + (i % 4)}
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

    print("  Phase 4 — HTTP errors for dashboard % (4xx/5xx)...")
    emit_sales_http_errors(
        sales_url,
        catalog_url,
        buyer=buyers[0] if buyers else None,
        product_ids=product_ids,
    )

    print("  Phase 5 — clearing Sales, then Catalog...")
    clear_sales(sales_url, catalog_url, emit_errors=False)
    clear_catalog(catalog_url, emit_errors=False)
    print("  load test finished (Sales + Catalog cleared).")
