import os
import json
import numpy as np
import xgboost as xgb
from typing import Dict, Tuple
from services.feature_engine import FEATURE_ORDER
from config import settings

class RiskScorer:
    def __init__(self, model_path: str = None, threshold_path: str = None):
        self.model_path = model_path or settings.RISK_MODEL_PATH
        self.threshold_path = threshold_path or settings.RISK_THRESHOLD_PATH
        self.model = None
        self.base_threshold = 0.65
        self._load_model()

    def _load_model(self):
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_p = self.model_path
        if not os.path.exists(model_p):
            alt_p = os.path.join(backend_dir, "ml", "model.json")
            if os.path.exists(alt_p):
                model_p = alt_p

        if os.path.exists(model_p):
            self.model = xgb.XGBClassifier()
            self.model.load_model(model_p)
        else:
            print(f"Warning: Risk model not found at {self.model_path}. Please run backend/ml/train.py.")

        thresh_p = self.threshold_path
        if not os.path.exists(thresh_p):
            alt_t = os.path.join(backend_dir, "ml", "threshold.json")
            if os.path.exists(alt_t):
                thresh_p = alt_t

        if os.path.exists(thresh_p):
            try:
                with open(thresh_p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.base_threshold = float(data.get("threshold", 0.65))
            except Exception as e:
                print(f"Error loading threshold: {e}")

    def predict_risk(self, features: Dict[str, float]) -> Tuple[float, float]:
        """
        Returns (risk_score, base_threshold).
        """
        if self.model is None:
            self._load_model()

        if self.model is None:
            # Fallback baseline score if model is not yet compiled
            return (0.1, self.base_threshold)

        feature_vector = [features[k] for k in FEATURE_ORDER]
        X = np.array([feature_vector], dtype=float)
        prob = float(self.model.predict_proba(X)[0][1])
        return (prob, self.base_threshold)

# Global singleton
risk_scorer = RiskScorer()

