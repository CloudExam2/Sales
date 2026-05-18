import logging
import os
import time
from typing import List

import httpx
from fastapi import HTTPException

logger = logging.getLogger("sales.catalog")

CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://localhost:8000").rstrip("/")
CATALOG_TIMEOUT = float(os.getenv("CATALOG_TIMEOUT_SECONDS", "5"))


async def _catalog_get(path: str) -> httpx.Response:
    url = f"{CATALOG_SERVICE_URL}{path}"
    started = time.perf_counter()
    logger.info("catalog outbound GET %s", url)
    try:
        async with httpx.AsyncClient(timeout=CATALOG_TIMEOUT) as client:
            response = await client.get(url)
    except httpx.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.warning(
            "catalog outbound GET %s failed after %.1fms: %s",
            url,
            elapsed_ms,
            exc,
        )
        raise

    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "catalog outbound GET %s -> %s (%.1fms)",
        url,
        response.status_code,
        elapsed_ms,
    )
    return response


async def validate_catalog_entities(client_id: int, product_ids: List[int]) -> None:
    """Confirm the client and every product exist in Catalog before saving a sale."""
    logger.info(
        "catalog validate start client_id=%s product_ids=%s base_url=%s",
        client_id,
        product_ids,
        CATALOG_SERVICE_URL,
    )

    try:
        client_res = await _catalog_get(f"/clients/{client_id}")
        if client_res.status_code == 404:
            logger.warning("catalog validate client_id=%s not found", client_id)
            raise HTTPException(status_code=400, detail=f"Client {client_id} not found in Catalog")
        if client_res.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Catalog returned {client_res.status_code} for client {client_id}",
            )

        for p_id in product_ids:
            p_res = await _catalog_get(f"/products/{p_id}")
            if p_res.status_code == 404:
                logger.warning("catalog validate product_id=%s not found", p_id)
                raise HTTPException(status_code=400, detail=f"Product {p_id} not found in Catalog")
            if p_res.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Catalog returned {p_res.status_code} for product {p_id}",
                )
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.warning("Catalog unreachable at %s: %s", CATALOG_SERVICE_URL, e)
        raise HTTPException(status_code=502, detail=f"Catalog unreachable: {e}") from e

    logger.info(
        "catalog validate ok client_id=%s product_ids=%s",
        client_id,
        product_ids,
    )
