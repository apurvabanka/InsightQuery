from fastapi import FastAPI
from api.csv_routes import router as csv_router
from db.base import Base
from db.session import engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Insight Query", version="1.0.0")

app.include_router(csv_router, prefix="/api/csv", tags=["csv"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the CSV Upload API!"}
