import logging
import os
from typing import List

import httpx
from fastapi import HTTPException

logger = logging.getLogger("sales.catalog")

CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://localhost:8000").rstrip("/")
CATALOG_TIMEOUT = float(os.getenv("CATALOG_TIMEOUT_SECONDS", "5"))


async def validate_catalog_entities(client_id: int, product_ids: List[int]) -> None:
    """Confirm the client and every product exist in Catalog before saving a sale."""
    try:
        async with httpx.AsyncClient(timeout=CATALOG_TIMEOUT) as client:
            client_res = await client.get(f"{CATALOG_SERVICE_URL}/clients/{client_id}")
            if client_res.status_code == 404:
                raise HTTPException(status_code=400, detail=f"Client {client_id} not found in Catalog")
            if client_res.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Catalog returned {client_res.status_code} for client {client_id}",
                )

            for p_id in product_ids:
                p_res = await client.get(f"{CATALOG_SERVICE_URL}/products/{p_id}")
                if p_res.status_code == 404:
                    raise HTTPException(status_code=400, detail=f"Product {p_id} not found in Catalog")
                if p_res.status_code != 200:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Catalog returned {p_res.status_code} for product {p_id}",
                    )
    except httpx.HTTPError as e:
        logger.warning("Catalog unreachable at %s: %s", CATALOG_SERVICE_URL, e)
        raise HTTPException(status_code=502, detail=f"Catalog unreachable: {e}") from e
