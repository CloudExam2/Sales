import logging
import time

from fastapi import FastAPI, Request
from database import engine, Base
from routers import note_contents, sales

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

# Generate tables (for local dev)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sales Service")

app.include_router(note_contents.router, prefix="/note-contents", tags=["note-contents"])
app.include_router(sales.router, prefix="/sales", tags=["sales"])


@app.middleware("http")
async def log_sales_api(request: Request, call_next):
    """Log Sales API traffic (stdout → CloudWatch via Docker awslogs)."""
    started = time.perf_counter()
    response = await call_next(request)
    path = request.url.path
    if path.startswith(("/sales", "/note-contents")):
        ms = (time.perf_counter() - started) * 1000
        logging.getLogger("sales.api").info(
            "%s %s status=%s duration_ms=%.1f",
            request.method,
            path,
            response.status_code,
            ms,
        )
    return response


@app.get("/")
def health_check():
    return {"status": "healthy", "service": "sales"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
