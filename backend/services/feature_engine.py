import math
from datetime import datetime
from typing import Any, Dict, List, Union

FEATURE_ORDER: List[str] = [
    "amount_zscore",
    "amount_merchant_zscore",
    "velocity_1h",
    "velocity_24h",
    "same_merchant_txn_1h",
    "merchant_novelty",
    "category_novelty",
    "hour_of_day",
    "hour_deviation",
    "daily_spend_ratio",
    "log_amount"
]

def compute_features(
    amount: float,
    created_at: datetime,
    merchant_id: str,
    merchant_category: str,
    agent_rolling_mean: float,
    agent_rolling_std: float,
    agent_txn_last_1h: int,
    agent_txn_last_24h: int,
    agent_avg_hour: float,
    agent_std_hour: float,
    agent_known_merchants: List[str],
    agent_known_categories: List[str],
    agent_daily_spend_today: float,
    merchant_avg_amount: float,
    merchant_std_amount: float,
    same_merchant_txn_1h: int = 1
) -> Dict[str, float]:
    """
    Computes the exact 11 features for XGBoost in the specified order.
    """
    # 1. amount_zscore
    std_amount = max(float(agent_rolling_std or 1.0), 1.0)
    amount_zscore = float((amount - float(agent_rolling_mean or 0.0)) / std_amount)

    # 2. amount_merchant_zscore
    std_merch = max(float(merchant_std_amount or 1.0), 1.0)
    amount_merchant_zscore = float((amount - float(merchant_avg_amount or amount)) / std_merch)

    # 3. velocity_1h
    velocity_1h = float(agent_txn_last_1h)

    # 4. velocity_24h
    velocity_24h = float(agent_txn_last_24h)

    # 5. same_merchant_txn_1h
    same_merch_1h = float(same_merchant_txn_1h)

    # 6. merchant_novelty
    merchant_novelty = 0.0 if merchant_id in (agent_known_merchants or []) else 1.0

    # 7. category_novelty
    category_novelty = 0.0 if merchant_category in (agent_known_categories or []) else 1.0

    # 8. hour_of_day
    hour_of_day = float(created_at.hour + (created_at.minute / 60.0))

    # 9. hour_deviation
    std_hour = max(float(agent_std_hour or 1.0), 1.0)
    avg_hour = float(agent_avg_hour if agent_avg_hour is not None else 12.0)
    hour_deviation = float(abs(hour_of_day - avg_hour) / std_hour)

    # 10. daily_spend_ratio (ratio of today's total spend to 5x daily norm)
    base_daily_norm = max(float(agent_rolling_mean or 50.0) * 5.0, 1.0)
    daily_spend_ratio = float((float(agent_daily_spend_today or 0.0) + amount) / base_daily_norm)

    # 11. log_amount
    log_amount = float(math.log1p(max(amount, 0.0)))

    return {
        "amount_zscore": amount_zscore,
        "amount_merchant_zscore": amount_merchant_zscore,
        "velocity_1h": velocity_1h,
        "velocity_24h": velocity_24h,
        "same_merchant_txn_1h": same_merch_1h,
        "merchant_novelty": merchant_novelty,
        "category_novelty": category_novelty,
        "hour_of_day": hour_of_day,
        "hour_deviation": hour_deviation,
        "daily_spend_ratio": daily_spend_ratio,
        "log_amount": log_amount
    }

