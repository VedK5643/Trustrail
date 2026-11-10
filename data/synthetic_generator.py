import csv
import json
import math
import os
import random
import uuid
from datetime import datetime, timedelta, timezone

def generate_synthetic_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    merchants_path = os.path.join(base_dir, "merchants.json")
    output_dir = os.path.join(base_dir, "generated")
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, "synthetic_transactions.csv")

    with open(merchants_path, "r", encoding="utf-8") as f:
        all_merchants = json.load(f)

    # Segregate merchants by category and normal pools
    merch_by_id = {m["id"]: m for m in all_merchants}
    procurement_merch_ids = [m["id"] for m in all_merchants if m["id"].startswith("merch_off_") or m["id"].startswith("merch_elec_")][:10]
    subscription_merch_ids = [m["id"] for m in all_merchants if m["id"].startswith("merch_saas_")]
    travel_merch_ids = [m["id"] for m in all_merchants if m["id"].startswith("merch_trav_")]
    anomaly_merch_ids = [m["id"] for m in all_merchants if m["id"].startswith("merch_anom_") or m["id"] == "newvendor-gaming"]

    agent_profiles = {
        "procurement-agent": {
            "name": "Procurement Agent",
            "normal_merchants": procurement_merch_ids,
            "mean_amount": 85.0,
            "std_amount": 40.0,
            "min_amount": 5.0,
            "max_amount": 500.0,
            "start_hour": 9,
            "end_hour": 17,
            "weekdays_only": True,
            "daily_velocity_range": (2, 5),
            "descriptions": ["Bulk copy paper", "Ergonomic chair accessories", "HDMI adapters and cables", "Keyboards & mice set", "Desk organizer trays", "Printer ink cartridges"]
        },
        "subscription-agent": {
            "name": "Subscription Agent",
            "normal_merchants": subscription_merch_ids,
            "mean_amount": 29.0,
            "std_amount": 15.0,
            "min_amount": 5.0,
            "max_amount": 200.0,
            "start_hour": 0,
            "end_hour": 23,
            "weekdays_only": False,
            "daily_velocity_range": (1, 2),
            "descriptions": ["Monthly seat license renewal", "Cloud storage tier upgrade", "Developer tooling seat renewal", "Workspace enterprise subscription", "Security suite add-on"]
        },
        "travel-agent": {
            "name": "Travel Booking Agent",
            "normal_merchants": travel_merch_ids,
            "mean_amount": 350.0,
            "std_amount": 200.0,
            "min_amount": 50.0,
            "max_amount": 3000.0,
            "start_hour": 8,
            "end_hour": 20,
            "weekdays_only": False,
            "daily_velocity_range": (1, 3),
            "descriptions": ["Economy flight to Q3 summit", "Hotel lodging for client demo", "Rental car for site visit", "Executive train ticket", "Airport transit shuttle"]
        }
    }

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=90)
    all_rows = []

    for agent_id, prof in agent_profiles.items():
        agent_rows = []
        
        # 1. Generate 2,000 normal transactions
        for _ in range(2000):
            # Pick a day between start_time and now
            days_offset = random.uniform(0, 89)
            txn_date = start_time + timedelta(days=days_offset)
            
            # If weekdays only and landed on weekend, adjust
            if prof["weekdays_only"] and txn_date.weekday() >= 5:
                txn_date -= timedelta(days=2)

            # Hour
            hour = random.randint(prof["start_hour"], prof["end_hour"])
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            created_at = txn_date.replace(hour=hour, minute=minute, second=second, microsecond=0)

            # Amount
            amt = random.gauss(prof["mean_amount"], prof["std_amount"])
            amt = max(prof["min_amount"], min(prof["max_amount"], amt))
            amount = round(amt, 2)

            # Merchant
            merch_id = random.choice(prof["normal_merchants"])
            merch = merch_by_id[merch_id]

            agent_rows.append({
                "txn_id": f"txn_{uuid.uuid4().hex[:12]}",
                "agent_id": agent_id,
                "merchant_id": merch["id"],
                "merchant_name": merch["name"],
                "merchant_category": merch["category"],
                "amount": amount,
                "currency": "USD",
                "description": random.choice(prof["descriptions"]),
                "created_at": created_at.isoformat(),
                "is_anomaly": 0,
                "anomaly_type": ""
            })

        # 2. Inject 100 Anomalies
        # 30 Amount Spikes (5x - 20x mean)
        for _ in range(30):
            days_offset = random.uniform(5, 85)
            created_at = (start_time + timedelta(days=days_offset)).replace(
                hour=random.randint(prof["start_hour"], prof["end_hour"]),
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
                microsecond=0
            )
            multiplier = random.uniform(5.0, 20.0)
            amount = round(prof["mean_amount"] * multiplier, 2)
            merch_id = random.choice(prof["normal_merchants"])
            merch = merch_by_id[merch_id]

            agent_rows.append({
                "txn_id": f"txn_{uuid.uuid4().hex[:12]}",
                "agent_id": agent_id,
                "merchant_id": merch["id"],
                "merchant_name": merch["name"],
                "merchant_category": merch["category"],
                "amount": amount,
                "currency": "USD",
                "description": f"Expedited bulk order: {random.choice(prof['descriptions'])}",
                "created_at": created_at.isoformat(),
                "is_anomaly": 1,
                "anomaly_type": "amount_spike"
            })

        # 25 Velocity Bursts: 5 distinct runaway retry loops (5 rapid repeated charges per loop to the SAME merchant)
        for ep in range(5):
            burst_base_time = start_time + timedelta(days=random.uniform(5 + ep * 15, 14 + ep * 15))
            target_merch_id = random.choice(prof["normal_merchants"])
            target_merch = merch_by_id[target_merch_id]
            loop_amount = round(max(prof["min_amount"], random.gauss(prof["mean_amount"], prof["std_amount"] * 0.1)), 2)

            for i in range(5):
                offset_seconds = i * random.randint(20, 60)  # within 1-5 minutes
                created_at = (burst_base_time + timedelta(seconds=offset_seconds)).replace(microsecond=0)

                agent_rows.append({
                    "txn_id": f"txn_{uuid.uuid4().hex[:12]}",
                    "agent_id": agent_id,
                    "merchant_id": target_merch["id"],
                    "merchant_name": target_merch["name"],
                    "merchant_category": target_merch["category"],
                    "amount": loop_amount,
                    "currency": "USD",
                    "description": f"Automated recurring retry #{i+1}",
                    "created_at": created_at.isoformat(),
                    "is_anomaly": 1,
                    "anomaly_type": "velocity_burst"
                })

        # 20 Unknown Merchants
        for _ in range(20):
            days_offset = random.uniform(5, 85)
            created_at = (start_time + timedelta(days=days_offset)).replace(
                hour=random.randint(prof["start_hour"], prof["end_hour"]),
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
                microsecond=0
            )
            other_merchants = [m for m in all_merchants if m["id"] not in prof["normal_merchants"]]
            merch = random.choice(other_merchants)
            amt = random.uniform(merch["typical_amount_range"][0], merch["typical_amount_range"][1])

            agent_rows.append({
                "txn_id": f"txn_{uuid.uuid4().hex[:12]}",
                "agent_id": agent_id,
                "merchant_id": merch["id"],
                "merchant_name": merch["name"],
                "merchant_category": merch["category"],
                "amount": round(amt, 2),
                "currency": "USD",
                "description": f"One-off acquisition: {merch['name']}",
                "created_at": created_at.isoformat(),
                "is_anomaly": 1,
                "anomaly_type": "unknown_merchant"
            })

        # 15 Off-Hours
        for _ in range(15):
            days_offset = random.uniform(5, 85)
            # Pick hours strictly between 2 AM and 5 AM UTC
            hour = random.randint(2, 5)
            created_at = (start_time + timedelta(days=days_offset)).replace(
                hour=hour,
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
                microsecond=0
            )
            merch_id = random.choice(prof["normal_merchants"])
            merch = merch_by_id[merch_id]
            amount = round(max(prof["min_amount"], random.gauss(prof["mean_amount"], prof["std_amount"])), 2)

            agent_rows.append({
                "txn_id": f"txn_{uuid.uuid4().hex[:12]}",
                "agent_id": agent_id,
                "merchant_id": merch["id"],
                "merchant_name": merch["name"],
                "merchant_category": merch["category"],
                "amount": amount,
                "currency": "USD",
                "description": f"Late-night scheduled sync: {merch['name']}",
                "created_at": created_at.isoformat(),
                "is_anomaly": 1,
                "anomaly_type": "off_hours"
            })

        # 10 Category Drift
        for _ in range(10):
            days_offset = random.uniform(5, 85)
            created_at = (start_time + timedelta(days=days_offset)).replace(
                hour=random.randint(prof["start_hour"], prof["end_hour"]),
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
                microsecond=0
            )
            merch = merch_by_id[random.choice(anomaly_merch_ids)]
            amt = random.uniform(merch["typical_amount_range"][0], merch["typical_amount_range"][1])

            agent_rows.append({
                "txn_id": f"txn_{uuid.uuid4().hex[:12]}",
                "agent_id": agent_id,
                "merchant_id": merch["id"],
                "merchant_name": merch["name"],
                "merchant_category": merch["category"],
                "amount": round(amt, 2),
                "currency": "USD",
                "description": f"Unusual line-item expenditure: {merch['name']}",
                "created_at": created_at.isoformat(),
                "is_anomaly": 1,
                "anomaly_type": "category_drift"
            })

        all_rows.extend(agent_rows)

    # Sort all rows strictly chronologically
    all_rows.sort(key=lambda r: r["created_at"])

    # Write out CSV
    fieldnames = [
        "txn_id", "agent_id", "merchant_id", "merchant_name", "merchant_category",
        "amount", "currency", "description", "created_at", "is_anomaly", "anomaly_type"
    ]

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Generated {len(all_rows)} synthetic transactions at: {output_csv}")
    return output_csv

if __name__ == "__main__":
    generate_synthetic_data()

