from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from db.engine import get_db
from db.models import Transaction
from services.orchestrator import orchestrator

router = APIRouter(tags=["Transactions"])

class EvaluateRequest(BaseModel):
    paypal_order_id: str
    paypal_auth_id: str
    agent_id: str
    merchant_id: str
    merchant_name: str
    merchant_category: str
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    description: Optional[str] = ""

@router.post("/api/evaluate")
async def evaluate_transaction(
    payload: EvaluateRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await orchestrator.evaluate_transaction(
            db=db,
            paypal_order_id=payload.paypal_order_id,
            paypal_auth_id=payload.paypal_auth_id,
            agent_id=payload.agent_id,
            merchant_id=payload.merchant_id,
            merchant_name=payload.merchant_name,
            merchant_category=payload.merchant_category,
            amount=payload.amount,
            currency=payload.currency,
            description=payload.description or ""
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions")
async def list_transactions(
    limit: int = Query(50, ge=1, le=200),
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Transaction).order_by(desc(Transaction.created_at)).limit(limit)

    if agent_id and agent_id != "all":
        query = query.where(Transaction.agent_id == agent_id)

    if status and status != "all":
        query = query.where(Transaction.status == status.upper())

    result = await db.execute(query)
    txns = result.scalars().all()

    return [
        {
            "id": t.id,
            "paypal_order_id": t.paypal_order_id,
            "paypal_auth_id": t.paypal_auth_id,
            "paypal_capture_id": t.paypal_capture_id,
            "agent_id": t.agent_id,
            "merchant_id": t.merchant_id,
            "merchant_name": t.merchant_name,
            "merchant_category": t.merchant_category,
            "amount": float(t.amount),
            "currency": t.currency,
            "description": t.description,
            "status": t.status,
            "risk_score": float(t.risk_score) if t.risk_score is not None else None,
            "risk_threshold": float(t.risk_threshold) if t.risk_threshold is not None else None,
            "shap_explanation": t.shap_explanation,
            "policy_violations": t.policy_violations,
            "decision": t.decision,
            "decision_reason": t.decision_reason,
            "resolved_by": t.resolved_by,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None
        }
        for t in txns
    ]

