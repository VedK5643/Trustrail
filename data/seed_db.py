import csv
import json
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def seed_database():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir)
    load_dotenv(os.path.join(root_dir, ".env"))
    csv_path = os.path.join(base_dir, "generated", "synthetic_transactions.csv")

    if not os.path.exists(csv_path):
        print("CSV not found, generating first...")
        sys.path.insert(0, base_dir)
        from synthetic_generator import generate_synthetic_data
        csv_path = generate_synthetic_data()

    # Read db url from env or use unified backend SQLite path
    default_db_path = os.path.join(root_dir, "backend", "trustrail.db").replace("\\", "/")
    db_url = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{default_db_path}")
    # Convert async drivers to sync drivers for seeding
    sync_url = db_url.replace("+asyncpg", "").replace("+aiosqlite", "")

    print(f"Connecting to database: {sync_url}...")
    try:
        sys.path.insert(0, os.path.join(root_dir, "backend"))
        from db.engine import Base
        from db.models import Agent, Transaction, AgentRollingStats, MerchantHistory, Policy

        engine = create_engine(sync_url)
        Base.metadata.create_all(engine)
        print("Verified schema tables.")

        with engine.connect() as conn:
            # Seed baseline agents and agent-specific policies
            agent_defaults = [
                ("procurement-agent", "Procurement Agent", "Procures office supplies and operational hardware", 2000.0, 500.0, '["gambling", "crypto", "electronics_gaming"]'),
                ("subscription-agent", "Subscription Agent", "Manages cloud SaaS subscriptions and licenses", 1000.0, 200.0, '["gambling", "crypto"]'),
                ("travel-agent", "Travel Booking Agent", "Books corporate travel, flights, and hotels", 7500.0, 3500.0, '["gambling", "crypto", "electronics_gaming"]')
            ]

            for aid, aname, adesc, dcap, pcap, cdeny in agent_defaults:
                conn.execute(text("""
                    INSERT OR IGNORE INTO agents (id, name, description, trust_alpha, trust_beta, trust_score)
                    VALUES (:id, :name, :desc, 1.0, 1.0, 0.5);
                """ if "sqlite" in sync_url else """
                    INSERT INTO agents (id, name, description, trust_alpha, trust_beta, trust_score)
                    VALUES (:id, :name, :desc, 1.0, 1.0, 0.5)
                    ON CONFLICT (id) DO NOTHING;
                """), {"id": aid, "name": aname, "desc": adesc})

                conn.execute(text("""
                    INSERT OR REPLACE INTO policies (agent_id, daily_spend_cap, per_txn_cap, merchant_allowlist, merchant_denylist, category_allowlist, category_denylist)
                    VALUES (:id, :dcap, :pcap, '[]', '[]', '[]', :cdeny);
                """ if "sqlite" in sync_url else """
                    INSERT INTO policies (agent_id, daily_spend_cap, per_txn_cap, merchant_allowlist, merchant_denylist, category_allowlist, category_denylist)
                    VALUES (:id, :dcap, :pcap, '[]'::jsonb, '[]'::jsonb, '[]'::jsonb, CAST(:cdeny AS jsonb))
                    ON CONFLICT (agent_id) DO UPDATE
                    SET daily_spend_cap = EXCLUDED.daily_spend_cap,
                        per_txn_cap = EXCLUDED.per_txn_cap,
                        category_denylist = EXCLUDED.category_denylist;
                """), {"id": aid, "dcap": dcap, "pcap": pcap, "cdeny": cdeny})

                conn.execute(text("""
                    INSERT OR IGNORE INTO agent_rolling_stats (agent_id, known_merchants, known_categories)
                    VALUES (:id, '[]', '[]');
                """ if "sqlite" in sync_url else """
                    INSERT INTO agent_rolling_stats (agent_id)
                    VALUES (:id)
                    ON CONFLICT (agent_id) DO NOTHING;
                """), {"id": aid})

            conn.commit()

            # Load synthetic transactions
            df = pd.read_csv(csv_path)
            print(f"Loading {len(df)} transactions into database...")

            conn.execute(text("DELETE FROM transactions WHERE id LIKE 'txn_%';"))
            conn.commit()

            insert_sql = text("""
                INSERT OR IGNORE INTO transactions (
                    id, paypal_order_id, agent_id, merchant_id, merchant_name,
                    merchant_category, amount, currency, description, status,
                    created_at, decided_at, resolved_at, resolved_by, decision
                ) VALUES (
                    :id, :paypal_order_id, :agent_id, :merchant_id, :merchant_name,
                    :merchant_category, :amount, :currency, :description, :status,
                    :created_at, :decided_at, :resolved_at, 'SYSTEM', :decision
                );
            """ if "sqlite" in sync_url else """
                INSERT INTO transactions (
                    id, paypal_order_id, agent_id, merchant_id, merchant_name,
                    merchant_category, amount, currency, description, status,
                    created_at, decided_at, resolved_at, resolved_by, decision
                ) VALUES (
                    :id, :paypal_order_id, :agent_id, :merchant_id, :merchant_name,
                    :merchant_category, :amount, :currency, :description, :status,
                    :created_at, :decided_at, :resolved_at, 'SYSTEM', :decision
                ) ON CONFLICT (paypal_order_id) DO NOTHING;
            """)

            records = []
            for _, r in df.iterrows():
                is_anom = int(r["is_anomaly"])
                status = "DENIED" if is_anom else "CAPTURED"
                decision = "HOLD" if is_anom else "AUTO_CLEAR"
                records.append({
                    "id": r["txn_id"],
                    "paypal_order_id": f"ORD_{r['txn_id'][4:]}",
                    "agent_id": r["agent_id"],
                    "merchant_id": r["merchant_id"],
                    "merchant_name": r["merchant_name"],
                    "merchant_category": r["merchant_category"],
                    "amount": float(r["amount"]),
                    "currency": r["currency"],
                    "description": r["description"],
                    "status": status,
                    "created_at": r["created_at"],
                    "decided_at": r["created_at"],
                    "resolved_at": r["created_at"],
                    "decision": decision
                })

            conn.execute(insert_sql, records)
            conn.commit()
            print(f"Successfully inserted {len(records)} transactions.")

            # Compute and update rolling stats per agent
            for agent_id, group in df.groupby("agent_id"):
                normal_group = group[group["is_anomaly"] == 0]
                amounts = normal_group["amount"].tolist()
                mean_amt = float(np.mean(amounts)) if amounts else 85.0
                std_amt = float(np.std(amounts)) if len(amounts) > 1 else 30.0
                known_m = json.dumps(list(set(normal_group["merchant_id"].tolist())))
                known_c = json.dumps(list(set(normal_group["merchant_category"].tolist())))

                if "sqlite" in sync_url:
                    conn.execute(text("""
                        INSERT OR REPLACE INTO agent_rolling_stats (
                            agent_id, txn_count, rolling_mean_amount, rolling_std_amount,
                            txn_last_1h, txn_last_24h, avg_hour_of_day, std_hour_of_day,
                            known_merchants, known_categories, daily_spend_today, last_updated
                        ) VALUES (
                            :agent_id, :count, :mean, :std,
                            0, 0, 12.0, 4.0,
                            :merchants, :categories, 0.0, CURRENT_TIMESTAMP
                        );
                    """), {
                        "count": len(group),
                        "mean": round(mean_amt, 4),
                        "std": round(std_amt, 4),
                        "merchants": known_m,
                        "categories": known_c,
                        "agent_id": agent_id
                    })
                else:
                    conn.execute(text("""
                        INSERT INTO agent_rolling_stats (
                            agent_id, txn_count, rolling_mean_amount, rolling_std_amount,
                            known_merchants, known_categories, last_updated
                        ) VALUES (
                            :agent_id, :count, :mean, :std, CAST(:merchants AS jsonb), CAST(:categories AS jsonb), NOW()
                        ) ON CONFLICT (agent_id) DO UPDATE
                        SET txn_count = EXCLUDED.txn_count,
                            rolling_mean_amount = EXCLUDED.rolling_mean_amount,
                            rolling_std_amount = EXCLUDED.rolling_std_amount,
                            known_merchants = EXCLUDED.known_merchants,
                            known_categories = EXCLUDED.known_categories,
                            last_updated = NOW();
                    """), {
                        "count": len(group),
                        "mean": round(mean_amt, 4),
                        "std": round(std_amt, 4),
                        "merchants": known_m,
                        "categories": known_c,
                        "agent_id": agent_id
                    })

            # Compute and update merchant history
            for merch_id, group in df.groupby("merchant_id"):
                first = group.iloc[0]
                m_mean = float(np.mean(group["amount"]))
                m_std = float(np.std(group["amount"])) if len(group) > 1 else 15.0

                if "sqlite" in sync_url:
                    conn.execute(text("""
                        INSERT OR REPLACE INTO merchant_history (
                            merchant_id, merchant_name, category, txn_count, avg_amount, std_amount, last_seen
                        ) VALUES (
                            :id, :name, :cat, :count, :avg, :std, CURRENT_TIMESTAMP
                        );
                    """), {
                        "id": merch_id,
                        "name": first["merchant_name"],
                        "cat": first["merchant_category"],
                        "count": len(group),
                        "avg": round(m_mean, 4),
                        "std": round(m_std, 4)
                    })
                else:
                    conn.execute(text("""
                        INSERT INTO merchant_history (
                            merchant_id, merchant_name, category, txn_count, avg_amount, std_amount, last_seen
                        ) VALUES (
                            :id, :name, :cat, :count, :avg, :std, NOW()
                        ) ON CONFLICT (merchant_id) DO UPDATE
                        SET txn_count = EXCLUDED.txn_count,
                            avg_amount = EXCLUDED.avg_amount,
                            std_amount = EXCLUDED.std_amount,
                            last_seen = NOW();
                    """), {
                        "id": merch_id,
                        "name": first["merchant_name"],
                        "cat": first["merchant_category"],
                        "count": len(group),
                        "avg": round(m_mean, 4),
                        "std": round(m_std, 4)
                    })

            conn.commit()
            print("Successfully populated agent rolling stats and merchant history.")

    except Exception as e:
        print(f"Note: Database seeding skipped or failed (Postgres may not be running locally yet): {e}")

if __name__ == "__main__":
    seed_database()

