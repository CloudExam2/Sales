"""Unit tests for SQS payload (no AWS)."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.ephemeral

from sqs_notify import publish_sale_created, sale_to_message


def test_sale_to_message_shape():
    note = MagicMock()
    note.id = 7
    note.folio = "F-001"
    note.client_id = 1
    note.fac_address_id = 2
    note.send_address_id = 3
    note.total = Decimal("106.00")
    line = MagicMock()
    line.product_id = 100
    line.quantity = 2
    line.unit_price = Decimal("45.50")
    line.total = Decimal("91.00")
    note.contents = [line]

    msg = sale_to_message(note)
    assert msg["event"] == "sale_created"
    assert msg["sale_id"] == 7
    assert msg["folio"] == "F-001"
    assert msg["contents"][0]["product_id"] == 100


@patch(
    "sqs_notify.SQS_QUEUE_URL",
    "https://sqs.us-east-1.amazonaws.com/123/sales-ticket-queue",
)
@patch("sqs_notify.boto3.client")
def test_publish_sale_created_sends(mock_boto_client):
    mock_sqs = MagicMock()
    mock_boto_client.return_value = mock_sqs
    mock_sqs.send_message.return_value = {"MessageId": "abc"}

    note = MagicMock()
    note.id = 1
    note.folio = "F-X"
    note.client_id = 1
    note.fac_address_id = 1
    note.send_address_id = 1
    note.total = Decimal("10")
    note.contents = []

    assert publish_sale_created(note) is True
    mock_sqs.send_message.assert_called_once()
    body = mock_sqs.send_message.call_args.kwargs["MessageBody"]
    assert "sale_created" in body
    assert "F-X" in body
