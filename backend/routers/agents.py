from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.engine import get_db
from db.models import Agent, AgentRollingStats
from services.trust_score import trust_score_service

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.get("")
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Agent, AgentRollingStats)
        .outerjoin(AgentRollingStats, AgentRollingStats.agent_id == Agent.id)
        .order_by(Agent.id)
    )
    rows = result.all()

    output = []
    for a, st in rows:
        alpha, beta, score = trust_score_service.calculate_decay(
            float(a.trust_alpha),
            float(a.trust_beta),
            a.trust_updated_at
        )

        output.append({
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "trust_score": float(score),
            "trust_alpha": float(alpha),
            "trust_beta": float(beta),
            "txn_count": st.txn_count if st else 0,
            "rolling_mean_amount": float(st.rolling_mean_amount) if st else 0.0,
            "daily_spend_today": float(st.daily_spend_today) if st else 0.0,
            "known_merchants_count": len(st.known_merchants or []) if st else 0
        })

    return output

