import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from db.models import Transaction, AgentRollingStats, MerchantHistory, Agent
from services.feature_engine import compute_features
from services.policy_engine import policy_engine
from services.risk_scorer import risk_scorer
from services.shap_explainer import shap_explainer
from services.trust_score import trust_score_service
from services.paypal_service import paypal_service

class Orchestrator:
    @staticmethod
    async def evaluate_transaction(
        db: AsyncSession,
        paypal_order_id: str,
        paypal_auth_id: str,
        agent_id: str,
        merchant_id: str,
        merchant_name: str,
        merchant_category: str,
        amount: float,
        currency: str = "USD",
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Full authorize -> policy -> score -> capture/hold loop.
        """
        now = datetime.now(timezone.utc)
        txn_id = f"tr_{uuid.uuid4().hex[:12]}"

        # 1. Fetch or initialize AgentRollingStats
        stats_res = await db.execute(select(AgentRollingStats).where(AgentRollingStats.agent_id == agent_id))
        agent_stats = stats_res.scalar_one_or_none()
        if not agent_stats:
            agent_stats = AgentRollingStats(agent_id=agent_id)
            db.add(agent_stats)
            await db.flush()

        # Compute dynamic 1h, 24h, and same-merchant velocity from recent transactions
        one_hour_ago = now - timedelta(hours=1)
        twenty_four_hours_ago = now - timedelta(hours=24)

        v1h_res = await db.execute(
            select(func.count(Transaction.id)).where(
                and_(Transaction.agent_id == agent_id, Transaction.created_at >= one_hour_ago)
            )
        )
        v1h = (v1h_res.scalar() or 0) + 1  # include current txn

        v24h_res = await db.execute(
            select(func.count(Transaction.id)).where(
                and_(Transaction.agent_id == agent_id, Transaction.created_at >= twenty_four_hours_ago)
            )
        )
        v24h = (v24h_res.scalar() or 0) + 1

        same_merch_res = await db.execute(
            select(func.count(Transaction.id)).where(
                and_(
                    Transaction.agent_id == agent_id,
                    Transaction.merchant_id == merchant_id,
                    Transaction.created_at >= one_hour_ago
                )
            )
        )
        same_merch_v1h = (same_merch_res.scalar() or 0) + 1

        # Dynamic daily spend tracking for calendar today (00:00 UTC)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_spend_res = await db.execute(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.agent_id == agent_id,
                    Transaction.created_at >= start_of_today,
                    Transaction.status.in_(["CAPTURED", "AUTO_CAPTURED", "HELD"])
                )
            )
        )
        daily_spend_today = float(today_spend_res.scalar() or 0.0)
        agent_stats.daily_spend_today = daily_spend_today

        # Fetch or initialize MerchantHistory
        merch_res = await db.execute(select(MerchantHistory).where(MerchantHistory.merchant_id == merchant_id))
        merch_stats = merch_res.scalar_one_or_none()
        if not merch_stats:
            merch_stats = MerchantHistory(
                merchant_id=merchant_id,
                merchant_name=merchant_name,
                category=merchant_category,
                txn_count=0,
                avg_amount=amount,
                std_amount=max(amount * 0.2, 10.0)
            )
            db.add(merch_stats)
            await db.flush()

        # 2. Policy-as-Code Evaluation
        violations = await policy_engine.evaluate_policy(
            db=db,
            agent_id=agent_id,
            amount=amount,
            merchant_id=merchant_id,
            merchant_name=merchant_name,
            merchant_category=merchant_category,
            daily_spend_today=float(agent_stats.daily_spend_today)
        )

        txn = Transaction(
            id=txn_id,
            paypal_order_id=paypal_order_id,
            paypal_auth_id=paypal_auth_id,
            agent_id=agent_id,
            merchant_id=merchant_id,
            merchant_name=merchant_name,
            merchant_category=merchant_category,
            amount=amount,
            currency=currency,
            description=description,
            created_at=now,
            authorized_at=now
        )

        # 3. Always Compute 11-Feature Vector (even if policy flags, so ML explainability is never bypassed)
        known_merchants = agent_stats.known_merchants or []
        known_categories = agent_stats.known_categories or []

        features = compute_features(
            amount=amount,
            created_at=now,
            merchant_id=merchant_id,
            merchant_category=merchant_category,
            agent_rolling_mean=float(agent_stats.rolling_mean_amount),
            agent_rolling_std=float(agent_stats.rolling_std_amount),
            agent_txn_last_1h=v1h,
            agent_txn_last_24h=v24h,
            agent_avg_hour=float(agent_stats.avg_hour_of_day),
            agent_std_hour=float(agent_stats.std_hour_of_day),
            agent_known_merchants=known_merchants,
            agent_known_categories=known_categories,
            agent_daily_spend_today=float(agent_stats.daily_spend_today),
            merchant_avg_amount=float(merch_stats.avg_amount),
            merchant_std_amount=float(merch_stats.std_amount),
            same_merchant_txn_1h=same_merch_v1h
        )

        # 4. Predict Risk & Compute Trust-Adjusted Effective Threshold
        risk_score, base_threshold = risk_scorer.predict_risk(features)
        trust_score, alpha, beta = await trust_score_service.get_agent_trust(db, agent_id)
        effective_thresh = trust_score_service.effective_threshold(base_threshold, trust_score)

        txn.risk_score = risk_score
        txn.risk_threshold = effective_thresh
        txn.decided_at = now

        context = {
            "amount": amount,
            "merchant_name": merchant_name,
            "merchant_category": merchant_category,
            "agent_rolling_mean": float(agent_stats.rolling_mean_amount),
            "agent_rolling_std": float(agent_stats.rolling_std_amount),
            "agent_avg_hour": float(agent_stats.avg_hour_of_day),
            "agent_daily_spend_today": float(agent_stats.daily_spend_today),
            "merchant_avg_amount": float(merch_stats.avg_amount),
            "merchant_std_amount": float(merch_stats.std_amount)
        }

        # 5. Always Generate SHAP Explanation when flagged by policy or high risk
        shap_result = shap_explainer.explain(features, context, effective_thresh)
        txn.shap_explanation = shap_result

        # 6. Final Decision & Enforcement
        is_elevated_velocity = (same_merch_v1h > 1 or v1h > 3)

        if violations:
            # Policy Breach: void authorization on PayPal immediately
            await paypal_service.void_authorization(paypal_auth_id)
            txn.status = "VOIDED"
            txn.decision = "POLICY_BLOCK"
            txn.decision_reason = f"Blocked by policy: {violations[0]['detail']} | Risk: {risk_score * 100:.1f}%"
            txn.policy_violations = violations
            txn.resolved_by = "SYSTEM"
            txn.resolved_at = now

            # Trust penalty for policy breach
            await trust_score_service.update_trust_outcome(db, agent_id, "POLICY_BLOCK")

        elif risk_score < effective_thresh:
            # Low Risk & No Policy Breach: Auto-clear & capture authorization immediately
            cap_resp = await paypal_service.capture_authorization(paypal_auth_id)
            txn.paypal_capture_id = cap_resp.get("id")
            txn.status = "AUTO_CAPTURED"
            txn.decision = "AUTO_CLEAR"
            txn.decision_reason = f"Risk score ({risk_score:.3f}) below dynamic threshold ({effective_thresh:.3f})"
            txn.resolved_by = "SYSTEM"
            txn.resolved_at = now

            # Update rolling stats
            await Orchestrator._update_stats_success(db, agent_stats, merch_stats, amount, merchant_id, merchant_category, now, v1h, v24h)
            
            # Trust score update (frozen if in elevated burst, +0.05 otherwise)
            await trust_score_service.update_trust_outcome(db, agent_id, "AUTO_CAPTURED", is_elevated_velocity=is_elevated_velocity)

        else:
            # High Risk without hard policy breach: HOLD for human compliance review
            txn.status = "HELD"
            txn.decision = "HOLD"
            txn.decision_reason = f"Risk score ({risk_score:.3f}) exceeded dynamic threshold ({effective_thresh:.3f})"

        db.add(txn)
        await db.commit()

        return {
            "id": txn.id,
            "paypal_order_id": txn.paypal_order_id,
            "paypal_auth_id": txn.paypal_auth_id,
            "paypal_capture_id": txn.paypal_capture_id,
            "status": txn.status,
            "decision": txn.decision,
            "decision_reason": txn.decision_reason,
            "policy_violations": txn.policy_violations or [],
            "risk_score": float(txn.risk_score) if txn.risk_score is not None else 0.0,
            "risk_threshold": float(txn.risk_threshold) if txn.risk_threshold is not None else 0.0,
            "shap_explanation": txn.shap_explanation,
            "amount": float(txn.amount),
            "agent_id": txn.agent_id,
            "merchant_name": txn.merchant_name
        }

    @staticmethod
    async def approve_transaction(db: AsyncSession, txn_id: str) -> Dict[str, Any]:
        result = await db.execute(select(Transaction).where(Transaction.id == txn_id))
        txn = result.scalar_one_or_none()
        if not txn:
            raise ValueError(f"Transaction {txn_id} not found")

        if txn.status != "HELD":
            raise ValueError(f"Transaction is in status {txn.status}, only HELD can be approved")

        now = datetime.now(timezone.utc)
        cap_resp = await paypal_service.capture_authorization(txn.paypal_auth_id)
        txn.paypal_capture_id = cap_resp.get("id")
        txn.status = "CAPTURED"
        txn.decision = "APPROVED"
        txn.resolved_by = "HUMAN"
        txn.resolved_at = now

        # Update stats
        stats_res = await db.execute(select(AgentRollingStats).where(AgentRollingStats.agent_id == txn.agent_id))
        agent_stats = stats_res.scalar_one_or_none()
        merch_res = await db.execute(select(MerchantHistory).where(MerchantHistory.merchant_id == txn.merchant_id))
        merch_stats = merch_res.scalar_one_or_none()

        if agent_stats and merch_stats:
            await Orchestrator._update_stats_success(
                db, agent_stats, merch_stats, float(txn.amount), txn.merchant_id, txn.merchant_category, now,
                int(agent_stats.txn_last_1h) + 1, int(agent_stats.txn_last_24h) + 1
            )

        # Trust score ticks UP (held then approved)
        await trust_score_service.update_trust_outcome(db, txn.agent_id, "APPROVED")
        await db.commit()

        return {"id": txn.id, "status": txn.status, "decision": txn.decision}

    @staticmethod
    async def deny_transaction(db: AsyncSession, txn_id: str) -> Dict[str, Any]:
        result = await db.execute(select(Transaction).where(Transaction.id == txn_id))
        txn = result.scalar_one_or_none()
        if not txn:
            raise ValueError(f"Transaction {txn_id} not found")

        if txn.status != "HELD":
            raise ValueError(f"Transaction is in status {txn.status}, only HELD can be denied")

        now = datetime.now(timezone.utc)
        await paypal_service.void_authorization(txn.paypal_auth_id)
        txn.status = "VOIDED"
        txn.decision = "DENIED"
        txn.resolved_by = "HUMAN"
        txn.resolved_at = now

        # Trust score ticks DOWN heavily (held then denied)
        await trust_score_service.update_trust_outcome(db, txn.agent_id, "DENIED")
        await db.commit()

        return {"id": txn.id, "status": txn.status, "decision": txn.decision}

    @staticmethod
    async def _update_stats_success(
        db: AsyncSession,
        agent_stats: AgentRollingStats,
        merch_stats: MerchantHistory,
        amount: float,
        merchant_id: str,
        merchant_category: str,
        now: datetime,
        v1h: int,
        v24h: int
    ):
        # Update agent stats
        prev_count = agent_stats.txn_count
        new_count = prev_count + 1
        agent_stats.txn_count = new_count
        agent_stats.txn_last_1h = v1h
        agent_stats.txn_last_24h = v24h
        agent_stats.daily_spend_today = float(agent_stats.daily_spend_today) + amount

        # Incremental mean update
        old_mean = float(agent_stats.rolling_mean_amount)
        new_mean = old_mean + (amount - old_mean) / min(new_count, 100)
        agent_stats.rolling_mean_amount = new_mean

        # Merchants and categories
        merchs = list(agent_stats.known_merchants or [])
        if merchant_id not in merchs:
            merchs.append(merchant_id)
            agent_stats.known_merchants = merchs

        cats = list(agent_stats.known_categories or [])
        if merchant_category not in cats:
            cats.append(merchant_category)
            agent_stats.known_categories = cats

        agent_stats.last_updated = now

        # Update merchant stats
        m_count = merch_stats.txn_count + 1
        merch_stats.txn_count = m_count
        m_old_mean = float(merch_stats.avg_amount)
        merch_stats.avg_amount = m_old_mean + (amount - m_old_mean) / m_count
        merch_stats.last_seen = now

orchestrator = Orchestrator()

