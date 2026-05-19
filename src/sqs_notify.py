"""Publish sale-created events to Core SQS (Notification Lambda consumes the queue)."""

import json
import logging
import os
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger("sales.sqs")

SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL", "").strip()
AWS_REGION = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Object of type {type(value)} is not JSON serializable")


def sale_to_message(note) -> dict:
    """Build the JSON payload Notification Lambda formats into email."""
    lines = []
    for line in note.contents:
        lines.append(
            {
                "product_id": line.product_id,
                "quantity": line.quantity,
                "unit_price": line.unit_price,
                "line_total": line.total,
            }
        )
    return {
        "event": "sale_created",
        "sale_id": note.id,
        "folio": note.folio,
        "client_id": note.client_id,
        "fac_address_id": note.fac_address_id,
        "send_address_id": note.send_address_id,
        "total": note.total,
        "contents": lines,
    }


def publish_sale_created(note) -> bool:
    """
    Send sale JSON to sales-ticket-queue. Returns True if message was sent.
    Skips quietly when SQS_QUEUE_URL is unset (local dev / tests).
    """
    if not SQS_QUEUE_URL:
        logger.warning("SQS_QUEUE_URL not set on Sales container; skipping sale notification email")
        return False

    body = sale_to_message(note)
    try:
        client = boto3.client("sqs", region_name=AWS_REGION)
        resp = client.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(body, default=_json_default),
        )
        logger.info(
            "sqs sale_created sale_id=%s folio=%s message_id=%s",
            note.id,
            note.folio,
            resp.get("MessageId"),
        )
        return True
    except (ClientError, BotoCoreError) as exc:
        logger.warning("Failed to publish sale to SQS: %s", exc)
        return False
