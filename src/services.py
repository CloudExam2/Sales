import os
from typing import List

import httpx
from fastapi import HTTPException

CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://localhost:8000").rstrip("/")

async def validate_catalog_entities(client_id: int, product_ids: List[int]):
    async with httpx.AsyncClient() as client:
        # Validate Client
        client_res = await client.get(f"{CATALOG_SERVICE_URL}/clients/{client_id}")
        if client_res.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Client {client_id} not found in Catalog")

        # Validate Products
        for p_id in product_ids:
            p_res = await client.get(f"{CATALOG_SERVICE_URL}/products/{p_id}")
            if p_res.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Product {p_id} not found in Catalog")