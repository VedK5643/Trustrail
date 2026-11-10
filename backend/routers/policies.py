from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.engine import get_db
from db.models import Policy

router = APIRouter(prefix="/policies", tags=["Policies"])

class PolicyUpdateRequest(BaseModel):
    daily_spend_cap: Optional[float] = None
    per_txn_cap: Optional[float] = None
    merchant_allowlist: List[str] = []
    merchant_denylist: List[str] = []
    category_allowlist: List[str] = []
    category_denylist: List[str] = []

@router.get("/{agent_id}")
async def get_policy(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Policy).where(Policy.agent_id == agent_id))
    policy = result.scalar_one_or_none()

    if not policy:
        # Return default policy
        return {
            "agent_id": agent_id,
            "daily_spend_cap": None,
            "per_txn_cap": None,
            "merchant_allowlist": [],
            "merchant_denylist": [],
            "category_allowlist": [],
            "category_denylist": []
        }

    return {
        "agent_id": policy.agent_id,
        "daily_spend_cap": float(policy.daily_spend_cap) if policy.daily_spend_cap is not None else None,
        "per_txn_cap": float(policy.per_txn_cap) if policy.per_txn_cap is not None else None,
        "merchant_allowlist": policy.merchant_allowlist or [],
        "merchant_denylist": policy.merchant_denylist or [],
        "category_allowlist": policy.category_allowlist or [],
        "category_denylist": policy.category_denylist or [],
        "updated_at": policy.updated_at.isoformat() if policy.updated_at else None
    }

@router.put("/{agent_id}")
async def update_policy(
    agent_id: str,
    payload: PolicyUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Policy).where(Policy.agent_id == agent_id))
    policy = result.scalar_one_or_none()

    if not policy:
        policy = Policy(agent_id=agent_id)
        db.add(policy)

    policy.daily_spend_cap = payload.daily_spend_cap
    policy.per_txn_cap = payload.per_txn_cap
    policy.merchant_allowlist = payload.merchant_allowlist
    policy.merchant_denylist = payload.merchant_denylist
    policy.category_allowlist = payload.category_allowlist
    policy.category_denylist = payload.category_denylist
    policy.updated_at = datetime.now(timezone.utc)

    await db.commit()
    return {"status": "SUCCESS", "agent_id": agent_id}

