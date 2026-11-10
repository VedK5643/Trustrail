from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from db.engine import get_db
from services.paypal_service import paypal_service
from services.trust_score import trust_score_service

router = APIRouter(prefix="/disputes", tags=["Disputes"])

class DisputeResolutionRequest(BaseModel):
    agent_id: str
    outcome: str = "RESOLVED_BUYER_FAVOUR"  # or RESOLVED_SELLER_FAVOUR
    note: Optional[str] = "Customer dispute resolution outcome fed back into reputation engine"

@router.get("")
async def list_disputes():
    """
    Calls PayPal Customer Disputes API.
    """
    try:
        data = await paypal_service.list_disputes()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: str,
    payload: DisputeResolutionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Feeds real dispute outcome into Agent's Beta-distribution trust score.
    """
    outcome_key = (
        "DISPUTE_BUYER_FAVOUR"
        if "BUYER" in payload.outcome.upper()
        else "DISPUTE_SELLER_FAVOUR"
    )

    new_score, alpha, beta = await trust_score_service.update_trust_outcome(
        db=db,
        agent_id=payload.agent_id,
        outcome=outcome_key
    )

    return {
        "dispute_id": dispute_id,
        "agent_id": payload.agent_id,
        "outcome": outcome_key,
        "new_trust_score": float(new_score),
        "trust_alpha": float(alpha),
        "trust_beta": float(beta),
        "message": f"Dispute outcome processed. Trust score updated to {new_score * 100:.1f}%"
    }

