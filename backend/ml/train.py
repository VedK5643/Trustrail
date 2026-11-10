import os
import sys
import json
import math
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_curve, roc_auc_score, f1_score, classification_report
import xgboost as xgb

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.feature_engine import compute_features, FEATURE_ORDER

def train_risk_model():
    root_dir = os.path.dirname(backend_dir)
    data_path = os.path.join(root_dir, "data", "generated", "synthetic_transactions.csv")

    if not os.path.exists(data_path):
        print("Synthetic transactions CSV not found. Generating now...")
        sys.path.insert(0, os.path.join(root_dir, "data"))
        from synthetic_generator import generate_synthetic_data
        data_path = generate_synthetic_data()

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.sort_values("created_at").reset_index(drop=True)

    # Simulate chronological state per agent and per merchant to compute accurate historical features
    agent_state = {}
    merchant_state = {}

    feature_rows = []
    labels = []

    print("Simulating rolling window and computing 10-feature vectors...")
    for idx, row in df.iterrows():
        agent_id = row["agent_id"]
        merch_id = row["merchant_id"]
        amount = float(row["amount"])
        txn_time = row["created_at"]

        # Initialize agent state if new
        if agent_id not in agent_state:
            agent_state[agent_id] = {
                "amounts": [],
                "timestamps": [],
                "merchant_timestamps": {},
                "hours": [],
                "merchants": set(),
                "categories": set(),
                "daily_spend": 0.0,
                "current_day": txn_time.date()
            }

        ast = agent_state[agent_id]

        # Reset daily spend if day changed
        if txn_time.date() != ast["current_day"]:
            ast["daily_spend"] = 0.0
            ast["current_day"] = txn_time.date()

        # Prior window statistics (strictly prior to current transaction)
        amounts_window = ast["amounts"][-100:]
        if amounts_window:
            rolling_mean = float(np.mean(amounts_window))
            rolling_std = float(np.std(amounts_window)) if len(amounts_window) > 1 else 10.0
        else:
            rolling_mean = amount
            rolling_std = 15.0

        # Prior velocity
        one_hour_ago = txn_time - pd.Timedelta(hours=1)
        twenty_four_hours_ago = txn_time - pd.Timedelta(hours=24)
        
        # Count transactions in timestamps list
        v1h = sum(1 for t in ast["timestamps"] if t >= one_hour_ago)
        v24h = sum(1 for t in ast["timestamps"] if t >= twenty_four_hours_ago)

        # Same-merchant velocity in last 1 hour
        m_timestamps = ast.get("merchant_timestamps", {}).get(merch_id, [])
        same_m_1h = sum(1 for t in m_timestamps if t >= one_hour_ago) + 1

        # Prior hour stats
        if ast["hours"]:
            avg_hour = float(np.mean(ast["hours"]))
            std_hour = float(np.std(ast["hours"])) if len(ast["hours"]) > 1 else 4.0
        else:
            avg_hour = float(txn_time.hour)
            std_hour = 4.0

        # Merchant state
        if merch_id not in merchant_state:
            merchant_state[merch_id] = {"amounts": []}
        mst = merchant_state[merch_id]
        if mst["amounts"]:
            m_avg = float(np.mean(mst["amounts"]))
            m_std = float(np.std(mst["amounts"])) if len(mst["amounts"]) > 1 else 15.0
        else:
            m_avg = amount
            m_std = 20.0

        # Compute features
        feats = compute_features(
            amount=amount,
            created_at=txn_time,
            merchant_id=merch_id,
            merchant_category=row["merchant_category"],
            agent_rolling_mean=rolling_mean,
            agent_rolling_std=rolling_std,
            agent_txn_last_1h=v1h,
            agent_txn_last_24h=v24h,
            agent_avg_hour=avg_hour,
            agent_std_hour=std_hour,
            agent_known_merchants=list(ast["merchants"]),
            agent_known_categories=list(ast["categories"]),
            agent_daily_spend_today=ast["daily_spend"],
            merchant_avg_amount=m_avg,
            merchant_std_amount=m_std,
            same_merchant_txn_1h=same_m_1h
        )

        feature_vector = [feats[col] for col in FEATURE_ORDER]
        feature_rows.append(feature_vector)
        labels.append(int(row["is_anomaly"]))

        # Now update state with current transaction
        ast["amounts"].append(amount)
        ast["timestamps"].append(txn_time)
        if "merchant_timestamps" not in ast:
            ast["merchant_timestamps"] = {}
        if merch_id not in ast["merchant_timestamps"]:
            ast["merchant_timestamps"][merch_id] = []
        ast["merchant_timestamps"][merch_id].append(txn_time)

        ast["hours"].append(txn_time.hour + txn_time.minute / 60.0)
        ast["merchants"].add(merch_id)
        ast["categories"].add(row["merchant_category"])
        ast["daily_spend"] += amount

        mst["amounts"].append(amount)

    X = np.array(feature_rows)
    y = np.array(labels)

    print(f"Total samples: {len(y)}, Anomalies: {np.sum(y)} ({np.mean(y)*100:.2f}%)")

    # Stratified 80/20 train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )

    pos_count = np.sum(y_train == 1)
    neg_count = np.sum(y_train == 0)
    scale_pos = neg_count / max(pos_count, 1)

    print(f"Training XGBoost (scale_pos_weight: {scale_pos:.2f})...")
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos,
        eval_metric='aucpr',
        random_state=42
    )

    model.fit(X_train, y_train)

    # Evaluate probabilities on test set
    probs = model.predict_proba(X_test)[:, 1]
    roc_auc = roc_auc_score(y_test, probs)
    print(f"Test ROC-AUC: {roc_auc:.4f}")

    # Precision-Recall curve to find optimal threshold (>= 0.90 recall with highest precision)
    precisions, recalls, thresholds = precision_recall_curve(y_test, probs)
    
    chosen_threshold = 0.65 # Fallback default
    best_precision = 0.0

    for p, r, t in zip(precisions[:-1], recalls[:-1], thresholds):
        if r >= 0.90 and p > best_precision:
            best_precision = p
            chosen_threshold = float(t)

    print(f"Optimal threshold chosen: {chosen_threshold:.4f} (Recall: >=0.90, Precision: {best_precision:.4f})")

    # Evaluate at chosen threshold
    preds = (probs >= chosen_threshold).astype(int)
    print("\nClassification Report at chosen threshold:")
    print(classification_report(y_test, preds, target_names=["Normal", "Anomaly"]))

    # Output paths
    ml_dir = os.path.join(backend_dir, "ml")
    os.makedirs(ml_dir, exist_ok=True)
    model_path = os.path.join(ml_dir, "model.json")
    threshold_path = os.path.join(ml_dir, "threshold.json")

    model.save_model(model_path)
    with open(threshold_path, "w", encoding="utf-8") as f:
        json.dump({"threshold": round(chosen_threshold, 4), "roc_auc": round(roc_auc, 4)}, f, indent=2)

    print(f"Model saved to: {model_path}")
    print(f"Threshold saved to: {threshold_path}")

if __name__ == "__main__":
    train_risk_model()

