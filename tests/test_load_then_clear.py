"""
Bulk sales + Catalog validation stress on live EC2, then wipe both services.

Uses SALES_BASE_URL and CATALOG_BASE_URL from Sales/.env.

  copy .env.example .env   # set both Elastic IPs
  python tests/test_load_then_clear.py

Or: pytest tests/test_load_then_clear.py -v

Does NOT run in CI. Each POST /sales/ hits Catalog (client + every product line).
Watch CloudWatch → Exam2-EC2-Overview for CPU on Catalog and Sales.
"""

import pytest

from seed_helpers import get_catalog_url, get_sales_url, load_test_then_clear

pytestmark = pytest.mark.seed


def test_load_then_clear_sales_and_catalog():
    load_test_then_clear(get_sales_url(), get_catalog_url())


if __name__ == "__main__":
    load_test_then_clear()
