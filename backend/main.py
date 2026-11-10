import os
import sys

# Ensure backend directory is in python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from db.engine import engine, Base
from routers import (
    health_router,
    webhooks_router,
    transactions_router,
    decisions_router,
    agents_router,
    policies_router,
    disputes_router
)
from services.risk_scorer import risk_scorer
from services.shap_explainer import shap_explainer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database schema verified.")
    except Exception as e:
        print(f"Database connection note: {e}")

    # Check if ML model is ready
    if not os.path.exists(settings.RISK_MODEL_PATH):
        print("Risk model not found on startup. Attempting automated train...")
        try:
            from ml.train import train_risk_model
            train_risk_model()
            risk_scorer._load_model()
            shap_explainer._init_explainer()
        except Exception as te:
            print(f"ML training note: {te}")
    else:
        risk_scorer._load_model()
        shap_explainer._init_explainer()

    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="TrustRail — Spend Governance Firewall",
    description="Explainable spend-governance and reputation firewall for AI agents paying through PayPal.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(webhooks_router)
app.include_router(transactions_router)
app.include_router(decisions_router)
app.include_router(agents_router)
app.include_router(policies_router)
app.include_router(disputes_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

