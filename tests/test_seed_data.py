"""
Seed a running Sales server with one demo sales note. Requires a running Catalog too
(Sales validates client + product ids before saving).

  copy .env.example .env   # set SALES_BASE_URL and CATALOG_BASE_URL once
  python tests/test_seed_data.py

Or:

  pytest tests/test_seed_data.py -v

Does NOT run in CI. Data is left on the server on purpose.
"""

import pytest

from seed_helpers import get_catalog_url, get_sales_url, seed_sales

pytestmark = pytest.mark.seed


def test_seed_sales_note():
    seed_sales(get_sales_url(), get_catalog_url())


if __name__ == "__main__":
    seed_sales()
