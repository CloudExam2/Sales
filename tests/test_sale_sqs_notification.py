"""
Create exactly one sale on live Sales + Catalog → SQS → Notification Lambda → email.

Prerequisites:
  - Core, Catalog, Sales, Notifications deployed
  - SNS subscription confirmed for Exam2-Sales-Notifications
  - Notifications Lambda has SQS event source mapping enabled
  - Sales container has SQS_QUEUE_URL (Sales CI deploy sets from org variable)

  copy Sales/.env.example .env   # SALES_BASE_URL, CATALOG_BASE_URL

  python tests/test_sale_sqs_notification.py
  pytest tests/test_sale_sqs_notification.py -m seed -v
"""

import pytest

from seed_helpers import create_one_sale, get_catalog_url, get_sales_url

pytestmark = pytest.mark.seed


def test_one_sale_sends_sqs_notification():
  note = create_one_sale(get_sales_url(), get_catalog_url())
  assert note.get("id")
  print(
    "\n  Sale created — check inaki.medina@gmail.com in 1–3 min "
    f"(folio={note.get('folio')}, id={note.get('id')}).\n"
    "  CloudWatch → Sales logs: filter `sales.sqs` for MessageId.\n"
  )


if __name__ == "__main__":
  test_one_sale_sends_sqs_notification()
