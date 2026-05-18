from fastapi import FastAPI
from database import engine, Base
from routers import sales

# Generate tables (for local dev)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sales Service")

# Include Routers
app.include_router(sales.router, prefix="/sales", tags=["sales"])

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "sales"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)