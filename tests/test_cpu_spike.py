"""
Hammer Sales EC2 CPU (and Catalog via validation). Watch dashboard + CPU alarm email.

  python tests/test_cpu_spike.py

One-liner (PowerShell, from Sales folder with .env set):

  python -c "import os;from dotenv import load_dotenv;load_dotenv();import requests;u=os.environ['SALES_BASE_URL'].rstrip('/');[requests.get(f'{u}/sales/',timeout=60) for _ in range(500)]"
"""

import os
from concurrent.futures import ThreadPoolExecutor

import pytest
import requests

pytestmark = pytest.mark.seed

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

BASE = os.getenv("SALES_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
ROUNDS = int(os.getenv("CPU_SPIKE_ROUNDS", "500"))
WORKERS = int(os.getenv("CPU_SPIKE_WORKERS", "32"))


def _hit(_: int) -> None:
    requests.get(f"{BASE}/sales/", timeout=60)
    requests.get(f"{BASE}/", timeout=60)


def spike_sales_cpu() -> None:
    print(f"CPU spike on {BASE} — {ROUNDS} rounds, {WORKERS} workers")
    print("  Watch CloudWatch dashboard + email if CPU > 70% for 2 minutes.")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(_hit, range(ROUNDS)))
    print("  Done.")


def test_spike_sales_cpu():
    spike_sales_cpu()


if __name__ == "__main__":
    spike_sales_cpu()
