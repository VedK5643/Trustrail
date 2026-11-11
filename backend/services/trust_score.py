from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Agent

class TrustScoreService:
    @staticmethod
    def calculate_decay(alpha: float, beta: float, last_updated: datetime) -> tuple[float, float, float]:
        """
        Decays alpha and beta toward uniform prior (1.0, 1.0).
        Returns (new_alpha, new_beta, new_trust_score).
        """
        now = datetime.now(timezone.utc)
        if last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=timezone.utc)

        hours_since = max(0.0, (now - last_updated).total_seconds() / 3600.0)
        decay_factor = 0.999 ** hours_since

        new_alpha = 1.0 + (alpha - 1.0) * decay_factor
        new_beta = 1.0 + (beta - 1.0) * decay_factor
        score = new_alpha / (new_alpha + new_beta)

        return (round(new_alpha, 4), round(new_beta, 4), round(score, 4))

    @staticmethod
    def effective_threshold(base_threshold: float, trust_score: float) -> float:
        """
        Trusted agents get a higher threshold (more permissive).
        Untrusted agents get a lower threshold (more strict).
        Range adjustment: +/- 0.15.
        """
        adjustment = (trust_score - 0.5) * 0.3
        eff = base_threshold + adjustment
        return round(max(0.1, min(0.95, eff)), 4)

    @classmethod
    async def get_agent_trust(cls, db: AsyncSession, agent_id: str) -> tuple[float, float, float]:
        """
        Read-only trust lookup: fetches agent and applies time decay in memory
        without writing back to the database. Persistence only happens inside
        update_trust_outcome() after an actual transaction decision.
        """
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()

        if not agent:
            return (0.5, 1.0, 1.0)

        alpha, beta, score = cls.calculate_decay(
            float(agent.trust_alpha),
            float(agent.trust_beta),
            agent.trust_updated_at
        )

        return (score, alpha, beta)

    @classmethod
    async def update_trust_outcome(
        cls,
        db: AsyncSession,
        agent_id: str,
        outcome: str,
        is_elevated_velocity: bool = False
    ) -> tuple[float, float, float]:
        """
        Updates alpha and beta based on terminal decision outcome:
        - AUTO_CAPTURED: alpha += 0.05 (only if velocity is normal; frozen if elevated)
        - APPROVED (Held -> Approved): alpha += 0.5 (human review vindication)
        - DENIED (Held -> Denied): beta += 2.0
        - POLICY_BLOCKED: beta += 1.0
        """
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()

        if not agent:
            return (0.5, 1.0, 1.0)

        # Apply decay first
        alpha, beta, _ = cls.calculate_decay(
            float(agent.trust_alpha),
            float(agent.trust_beta),
            agent.trust_updated_at
        )

        if outcome == "AUTO_CAPTURED":
            # If in an active burst, freeze trust growth completely
            if not is_elevated_velocity:
                alpha += 0.05
        elif outcome in ("APPROVED", "CAPTURED"):
            alpha += 0.5
        elif outcome in ("DENIED", "VOIDED"):
            beta += 2.0
        elif outcome in ("POLICY_BLOCK", "POLICY_BLOCKED"):
            beta += 1.0
        elif outcome == "DISPUTE_BUYER_FAVOUR":
            beta += 3.0  # Ground-truth penalty for disputed transaction lost
        elif outcome == "DISPUTE_SELLER_FAVOUR":
            alpha += 1.0  # Ground-truth confirmation of merchant legitimacy

        score = alpha / (alpha + beta)

        agent.trust_alpha = round(alpha, 4)
        agent.trust_beta = round(beta, 4)
        agent.trust_score = round(score, 4)
        agent.trust_updated_at = datetime.now(timezone.utc)
        await db.commit()

        return (agent.trust_score, agent.trust_alpha, agent.trust_beta)

trust_score_service = TrustScoreService()

