from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from kseb_tariff import calculate_kseb_tariff
# Import Core Logic and Engine
from predictor import get_predictor
from pydantic import BaseModel, Field
from routers import appliances

# Initialize App & Predictor
predictor = get_predictor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all AI models on server startup to ensure fast first responses"""
    print("\n" + "=" * 50)
    print("      SMARTWATT AI ENGINE STARTUP")
    print("   (Hybrid AI + Inferred Physics Mode)")
    print("=" * 50 + "\n")
    predictor.preload_all_models()
    print("\n" + "=" * 50)
    print("      READY TO SERVE PREDICTIONS")
    print("=" * 50 + "\n")

    yield


app = FastAPI(title="SmartWatt AI Backend", lifespan=lifespan)
# Explicitly initialize predictor here to ensure singleton is warm,
# although the router also gets it.

# CORS (The Bouncer of the Club)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(appliances.router)


@app.get("/health")
async def health_check():
    """Lightweight health check for keep-alive pings"""
    return {"status": "ok", "service": "smartwatt-backend"}


@app.get("/")
def root():
    return {"status": "online", "message": "SmartWatt (Hybrid AI + Physics) is Active"}


# --- PYDANTIC MODELS (The Forms) ---
class HouseholdData(BaseModel):
    kwh: float = Field(
        ..., gt=0, description="Bi-monthly energy consumption in kWh must be positive"
    )


class BillResult(BaseModel):
    total: float
    monthly: float
    slab: str


@app.post("/calculate-bill", response_model=BillResult)
def get_bill(data: HouseholdData):
    """Calculates KSEB Bill based on total units"""
    try:
        # Reuse your existing kseb_tariff.py logic
        result = calculate_kseb_tariff(
            data.kwh / 2
        )  # Convert bi-monthly to monthly for calculation logic if needed
        return {
            "total": result["total"],
            "monthly": result["monthly_estimate"],
            "slab": result["slab"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
