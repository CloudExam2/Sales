"""
Delete every sales note on a running Sales server (Catalog data is left alone).

  python tests/test_clear_data.py

Or:

  pytest tests/test_clear_data.py -v

Does NOT run in CI.
"""

import pytest

from seed_helpers import clear_sales, get_sales_url

pytestmark = pytest.mark.seed


def test_clear_all_sales_notes():
    clear_sales(get_sales_url())


if __name__ == "__main__":
    clear_sales()
