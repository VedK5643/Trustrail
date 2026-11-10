from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Policy

AGENT_ALIASES: Dict[str, str] = {
    "travel-booking-agent": "travel-agent",
    "travel_agent": "travel-agent",
    "subscription_agent": "subscription-agent",
    "procurement_agent": "procurement-agent",
}

DEFAULT_POLICY_PROFILES: Dict[str, Dict[str, Any]] = {
    "travel-agent": {
        "per_txn_cap": 3500.0,
        "daily_spend_cap": 7500.0,
        "merchant_allowlist": [],
        "merchant_denylist": [],
        "category_allowlist": [],
        "category_denylist": ["gambling", "crypto", "electronics_gaming"]
    },
    "travel-booking-agent": {
        "per_txn_cap": 3500.0,
        "daily_spend_cap": 7500.0,
        "merchant_allowlist": [],
        "merchant_denylist": [],
        "category_allowlist": [],
        "category_denylist": ["gambling", "crypto", "electronics_gaming"]
    },
    "procurement-agent": {
        "per_txn_cap": 500.0,
        "daily_spend_cap": 2000.0,
        "merchant_allowlist": [],
        "merchant_denylist": ["newvendor-gaming"],
        "category_allowlist": [],
        "category_denylist": ["gambling", "crypto", "electronics_gaming"]
    },
    "subscription-agent": {
        "per_txn_cap": 200.0,
        "daily_spend_cap": 1000.0,
        "merchant_allowlist": [],
        "merchant_denylist": [],
        "category_allowlist": [],
        "category_denylist": ["gambling", "crypto"]
    },
    "default": {
        "per_txn_cap": 1000.0,
        "daily_spend_cap": 3000.0,
        "merchant_allowlist": [],
        "merchant_denylist": [],
        "category_allowlist": [],
        "category_denylist": ["gambling", "crypto"]
    }
}

class PolicyEngine:
    @staticmethod
    async def evaluate_policy(
        db: AsyncSession,
        agent_id: str,
        amount: float,
        merchant_id: str,
        merchant_name: str,
        merchant_category: str,
        daily_spend_today: float
    ) -> List[Dict[str, str]]:
        """
        Evaluates policy-as-code rules for an agent.
        Falls back from DB-stored policy to agent-specific in-code profiles,
        then to default general profile.
        Returns a list of violations (empty list if all pass).
        """
        canonical_id = AGENT_ALIASES.get(agent_id, agent_id)
        
        # 1. Look up policy in DB by requested agent_id or canonical alias
        result = await db.execute(
            select(Policy).where(Policy.agent_id.in_([agent_id, canonical_id]))
        )
        db_policy = result.scalars().first()

        # 2. Get baseline profile for this agent
        profile = (
            DEFAULT_POLICY_PROFILES.get(agent_id)
            or DEFAULT_POLICY_PROFILES.get(canonical_id)
            or DEFAULT_POLICY_PROFILES["default"]
        )

        per_txn_cap = float(db_policy.per_txn_cap) if db_policy and db_policy.per_txn_cap is not None else profile.get("per_txn_cap")
        daily_spend_cap = float(db_policy.daily_spend_cap) if db_policy and db_policy.daily_spend_cap is not None else profile.get("daily_spend_cap")
        merchant_denylist = (db_policy.merchant_denylist if db_policy and db_policy.merchant_denylist else None) or profile.get("merchant_denylist", [])
        merchant_allowlist = (db_policy.merchant_allowlist if db_policy and db_policy.merchant_allowlist else None) or profile.get("merchant_allowlist", [])
        category_denylist = (db_policy.category_denylist if db_policy and db_policy.category_denylist else None) or profile.get("category_denylist", [])
        category_allowlist = (db_policy.category_allowlist if db_policy and db_policy.category_allowlist else None) or profile.get("category_allowlist", [])

        violations = []

        # Rule 1. Per-transaction cap
        if per_txn_cap is not None and amount > per_txn_cap:
            violations.append({
                "rule": "per_txn_cap",
                "detail": f"Amount ${amount:,.2f} exceeds per-transaction cap of ${per_txn_cap:,.2f}"
            })

        # Rule 2. Daily spend cap
        projected_spend = daily_spend_today + amount
        if daily_spend_cap is not None and projected_spend > daily_spend_cap:
            violations.append({
                "rule": "daily_spend_cap",
                "detail": f"Cumulative spend (${projected_spend:,.2f}) would exceed daily cap of ${daily_spend_cap:,.2f}"
            })

        # Rule 3. Merchant denylist
        if merchant_id in merchant_denylist:
            violations.append({
                "rule": "merchant_denylist",
                "detail": f"Merchant '{merchant_name}' ({merchant_id}) is on the blocked denylist"
            })

        # Rule 4. Merchant allowlist
        if len(merchant_allowlist) > 0 and merchant_id not in merchant_allowlist:
            violations.append({
                "rule": "merchant_allowlist",
                "detail": f"Merchant '{merchant_name}' ({merchant_id}) is not on the authorized allowlist"
            })

        # Rule 5. Category denylist
        if merchant_category in category_denylist:
            violations.append({
                "rule": "category_denylist",
                "detail": f"Category '{merchant_category}' is explicitly denied by spend policy"
            })

        # Rule 6. Category allowlist
        if len(category_allowlist) > 0 and merchant_category not in category_allowlist:
            violations.append({
                "rule": "category_allowlist",
                "detail": f"Category '{merchant_category}' is not on the authorized category list"
            })

        return violations

policy_engine = PolicyEngine()

