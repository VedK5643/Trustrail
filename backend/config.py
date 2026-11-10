from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import Optional

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, "trustrail.db").replace("\\", "/")

def _resolve_backend_path(path_value: str) -> str:
    if os.path.isabs(path_value):
        return path_value
    candidate_backend = os.path.normpath(os.path.join(BASE_DIR, path_value))
    if os.path.exists(candidate_backend):
        return candidate_backend
    candidate_root = os.path.normpath(os.path.join(REPO_ROOT, path_value))
    if os.path.exists(candidate_root):
        return candidate_root
    return candidate_backend

class Settings(BaseSettings):
    PAYPAL_CLIENT_ID: str = "sandbox_client_id_placeholder"
    PAYPAL_CLIENT_SECRET: str = "sandbox_client_secret_placeholder"
    PAYPAL_SANDBOX_BASE_URL: str = "https://api-m.sandbox.paypal.com"
    PAYPAL_WEBHOOK_ID: str = "sandbox_webhook_id_placeholder"
    PAYPAL_SANDBOX_BUYER_EMAIL: str = "sb-buyer@personal.example.com"

    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH}"

    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"

    BACKEND_URL: str = "http://localhost:8000"
    RISK_MODEL_PATH: str = os.path.join(BASE_DIR, "ml", "model.json")
    RISK_THRESHOLD_PATH: str = os.path.join(BASE_DIR, "ml", "threshold.json")

    @field_validator("RISK_MODEL_PATH", "RISK_THRESHOLD_PATH", mode="before")
    @classmethod
    def resolve_ml_paths(cls, v: str) -> str:
        return _resolve_backend_path(v) if isinstance(v, str) else v

    class Config:
        env_file = [os.path.join(REPO_ROOT, ".env"), ".env", "../.env"]
        extra = "ignore"

settings = Settings()

