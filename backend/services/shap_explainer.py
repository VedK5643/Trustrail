import os
import math
import numpy as np
import shap
import xgboost as xgb
from typing import Dict, Any, List, Optional
from services.feature_engine import FEATURE_ORDER
from services.risk_scorer import risk_scorer

class ShapExplainerService:
    def __init__(self):
        self.explainer = None
        self._init_explainer()

    def _init_explainer(self):
        if risk_scorer.model is None:
            risk_scorer._load_model()
        if risk_scorer.model is not None:
            try:
                self.explainer = shap.TreeExplainer(risk_scorer.model)
            except Exception as e:
                print(f"Error initializing TreeExplainer: {e}")

    def explain(
        self,
        features: Dict[str, float],
        context: Dict[str, Any],
        effective_threshold: float
    ) -> Dict[str, Any]:
        """
        Computes SHAP feature importance, top-3 English sentences, and counterfactual text.
        """
        if self.explainer is None:
            self._init_explainer()

        feature_vector = [features[k] for k in FEATURE_ORDER]
        X = np.array([feature_vector], dtype=float)

        if self.explainer is not None:
            try:
                shap_raw = self.explainer.shap_values(X)
                # If shap_raw is a list (binary classification), take class 1
                if isinstance(shap_raw, list):
                    shap_vals = shap_raw[1][0]
                elif len(shap_raw.shape) == 2:
                    shap_vals = shap_raw[0]
                else:
                    shap_vals = shap_raw
            except Exception as e:
                print(f"SHAP value calculation error: {e}")
                shap_vals = np.zeros(len(FEATURE_ORDER))
        else:
            # Fallback heuristic SHAP approximation
            shap_vals = np.array([
                max(0.0, features["amount_zscore"] * 0.2),
                max(0.0, features["amount_merchant_zscore"] * 0.1),
                max(0.0, (features["velocity_1h"] - 2) * 0.15),
                max(0.0, (features["velocity_24h"] - 5) * 0.05),
                max(0.0, (features.get("same_merchant_txn_1h", 1.0) - 1.0) * 0.3),
                features["merchant_novelty"] * 0.25,
                features["category_novelty"] * 0.35,
                0.0,
                max(0.0, features["hour_deviation"] * 0.1),
                max(0.0, (features["daily_spend_ratio"] - 1.0) * 0.2),
                max(0.0, (features["log_amount"] - 5.0) * 0.1)
            ])

        # Filter only positive contributions (risk-increasing) and sort descending
        risk_increasing = []
        for i, feat_name in enumerate(FEATURE_ORDER):
            s_val = float(shap_vals[i])
            if s_val > 0.001:  # Only features increasing risk
                risk_increasing.append({
                    "name": feat_name,
                    "value": float(features[feat_name]),
                    "shap_value": s_val,
                    "index": i
                })

        risk_increasing.sort(key=lambda item: item["shap_value"], reverse=True)
        top_features = risk_increasing[:3]

        # Generate English explanation sentences
        explained_features = []
        for item in top_features:
            fname = item["name"]
            eng_sentence = self._render_template(fname, features, context)
            explained_features.append({
                "name": fname,
                "value": item["value"],
                "shap_value": round(item["shap_value"], 4),
                "english": eng_sentence
            })

        # Generate counterfactual perturbation
        counterfactual = self._compute_counterfactual(
            features=features,
            top_features=risk_increasing,
            context=context,
            threshold=effective_threshold
        )

        return {
            "features": explained_features,
            "counterfactual": counterfactual
        }

    def _render_template(self, feat_name: str, features: Dict[str, float], ctx: Dict[str, Any]) -> str:
        amount = ctx.get("amount", 0.0)
        mean_amt = ctx.get("agent_rolling_mean", 85.0)
        m_name = ctx.get("merchant_name", "this merchant")
        m_mean = ctx.get("merchant_avg_amount", 100.0)
        category = ctx.get("merchant_category", "unknown")

        if feat_name == "amount_zscore":
            z = features.get("amount_zscore", 0.0)
            return f"Transaction amount (${amount:,.2f}) is {z:.1f}x standard deviations above this agent's average (${mean_amt:,.0f})"
        
        elif feat_name == "amount_merchant_zscore":
            z = features.get("amount_merchant_zscore", 0.0)
            return f"Amount (${amount:,.2f}) is {z:.1f}x standard deviations above this merchant's average (${m_mean:,.0f})"
        
        elif feat_name == "velocity_1h":
            n = int(features.get("velocity_1h", 1))
            return f"{n} transactions in the last hour (normal: 1-2)"
        
        elif feat_name == "velocity_24h":
            n = int(features.get("velocity_24h", 1))
            return f"{n} transactions in the last 24 hours"
        
        elif feat_name == "same_merchant_txn_1h":
            n = int(features.get("same_merchant_txn_1h", 1))
            return f"{n} duplicate charges to {m_name} within the last hour"
        
        elif feat_name == "merchant_novelty":
            return f"First-time transaction with this merchant ({m_name})"
        
        elif feat_name == "category_novelty":
            return f"Agent has never transacted in category '{category}' before"
        
        elif feat_name == "hour_of_day":
            hh = int(features.get("hour_of_day", 12))
            mm = int((features.get("hour_of_day", 12) % 1) * 60)
            return f"Transaction at {hh:02d}:{mm:02d} UTC, outside normal operating hours"
        
        elif feat_name == "hour_deviation":
            z = features.get("hour_deviation", 0.0)
            return f"Transaction time is {z:.1f}x standard deviations from agent's usual time"
        
        elif feat_name == "daily_spend_ratio":
            ratio = features.get("daily_spend_ratio", 1.0)
            total = ctx.get("agent_daily_spend_today", 0.0) + amount
            return f"Today's cumulative spend (${total:,.0f}) is {ratio:.0%} of daily norm"
        
        elif feat_name == "log_amount":
            return f"Unusually large absolute amount (${amount:,.2f})"

        return f"Feature {feat_name} contributed significantly to risk elevation"

    def _compute_counterfactual(
        self,
        features: Dict[str, float],
        top_features: List[Dict[str, Any]],
        context: Dict[str, Any],
        threshold: float
    ) -> str:
        if not top_features or risk_scorer.model is None:
            return "Transaction cleared without critical risk flags."

        top_feature_name = top_features[0]["name"]
        agent_avg_hour = float(context.get("agent_avg_hour", 12.0))
        rolling_std = float(context.get("agent_rolling_std", 40.0))
        rolling_mean = float(context.get("agent_rolling_mean", 85.0))
        merch_std = float(context.get("merchant_std_amount", 50.0))
        merch_mean = float(context.get("merchant_avg_amount", 100.0))
        m_name = context.get("merchant_name", "this merchant")

        # Binary/categorical features directly flip to safe 0
        if top_feature_name == "merchant_novelty":
            test_f = features.copy()
            test_f["merchant_novelty"] = 0.0
            test_vec = [test_f[k] for k in FEATURE_ORDER]
            if float(risk_scorer.model.predict_proba([test_vec])[0][1]) < threshold:
                return "Would clear if this merchant were in the agent's known set (no amount change needed)"
            
        if top_feature_name == "category_novelty":
            test_f = features.copy()
            test_f["category_novelty"] = 0.0
            test_vec = [test_f[k] for k in FEATURE_ORDER]
            if float(risk_scorer.model.predict_proba([test_vec])[0][1]) < threshold:
                cat = context.get("merchant_category", "unknown")
                return f"Would clear if category '{cat}' were in the agent's prior history"

        SAFE_DIRECTION = {
            "amount_zscore": 0.0,
            "amount_merchant_zscore": 0.0,
            "velocity_1h": 1.0,
            "velocity_24h": 1.0,
            "same_merchant_txn_1h": 1.0,
            "merchant_novelty": 0.0,
            "category_novelty": 0.0,
            "hour_of_day": agent_avg_hour,
            "hour_deviation": 0.0,
            "daily_spend_ratio": 0.2,
            "log_amount": 3.0,
        }

        original_val = features[top_feature_name]
        safe_val = SAFE_DIRECTION.get(top_feature_name, 0.0)

        # Binary search 20 iterations
        low, high = min(original_val, safe_val), max(original_val, safe_val)
        cleared_boundary = None
        test_features = features.copy()

        for _ in range(20):
            mid = (low + high) / 2.0
            test_features[top_feature_name] = mid

            # If adjusting amount_zscore, synchronously adjust log_amount
            if top_feature_name == "amount_zscore":
                hypothetical_amt = max(0.0, mid * rolling_std + rolling_mean)
                test_features["log_amount"] = math.log1p(hypothetical_amt)

            test_vec = [test_features[k] for k in FEATURE_ORDER]
            prob = float(risk_scorer.model.predict_proba([test_vec])[0][1])

            if prob < threshold:
                cleared_boundary = mid
                # Try getting closer to original value
                if original_val > safe_val:
                    low = mid
                else:
                    high = mid
            else:
                # Still flagged, move closer to safe value
                if original_val > safe_val:
                    high = mid
                else:
                    low = mid

        if cleared_boundary is None:
            return "Multiple risk factors combine; no single change would clear this transaction."

        # Template counterfactual English
        if top_feature_name == "amount_zscore":
            target_amt = max(5.0, cleared_boundary * rolling_std + rolling_mean)
            return f"Would clear if amount were under ${target_amt:,.0f}"

        elif top_feature_name == "amount_merchant_zscore":
            target_amt = max(5.0, cleared_boundary * merch_std + merch_mean)
            return f"Would clear if amount were under ${target_amt:,.0f} (this merchant's norm)"

        elif top_feature_name == "velocity_1h":
            return f"Would clear if fewer than {max(1, int(math.ceil(cleared_boundary)))} transactions this hour"

        elif top_feature_name == "velocity_24h":
            return f"Would clear if fewer than {max(1, int(math.ceil(cleared_boundary)))} transactions today"

        elif top_feature_name == "same_merchant_txn_1h":
            return f"Would clear if no duplicate recurring transactions to {m_name} occurred within the same hour"

        elif top_feature_name == "hour_of_day":
            h1 = int(max(0, agent_avg_hour - 3))
            h2 = int(min(23, agent_avg_hour + 3))
            return f"Would clear if transacted between {h1:02d}:00 and {h2:02d}:00 UTC"

        elif top_feature_name == "hour_deviation":
            return f"Would clear if transacted closer to agent's usual hours ({agent_avg_hour:.0f}:00 UTC)"

        elif top_feature_name == "daily_spend_ratio":
            daily_norm = max(rolling_mean * 5.0, 1.0)
            max_daily = cleared_boundary * daily_norm
            return f"Would clear if today's total spend were under ${max_daily:,.0f}"

        elif top_feature_name == "log_amount":
            target_amt = math.expm1(cleared_boundary)
            return f"Would clear if amount were under ${target_amt:,.0f}"

        return "Would clear with minor parameter adjustments toward baseline behavior."

# Global singleton
shap_explainer = ShapExplainerService()

