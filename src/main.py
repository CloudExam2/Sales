from fastapi import FastAPI
from database import engine, Base
from routers import sales

# Generate tables (for local dev)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Catalog Service")

# Include Routers
app.include_router(sales.router)

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "catalog"}