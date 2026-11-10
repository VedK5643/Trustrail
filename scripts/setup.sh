#!/usr/bin/env bash
set -e

echo "============================================="
echo "  TrustRail — Spend Governance Setup Script  "
echo "============================================="

# 1. Start Postgres DB via Docker
echo -e "\n[1/5] Starting Postgres DB container..."
docker compose up -d db

echo "Waiting 5 seconds for Postgres to initialize..."
sleep 5

# 2. Python environment & dependencies
echo -e "\n[2/5] Installing backend dependencies..."
pip install -r backend/requirements.txt

# 3. Generate synthetic data & Train XGBoost
echo -e "\n[3/5] Generating synthetic transactions & Training ML Risk Model..."
python data/synthetic_generator.py
python backend/ml/train.py

# 4. Seed Database
echo -e "\n[4/5] Seeding database with historical agent & merchant data..."
python data/seed_db.py

# 5. Setup Agents & Dashboard
echo -e "\n[5/5] Installing Agent & Dashboard Node dependencies..."
cd agents && npm install && cd ..
cd dashboard && npm install && cd ..

echo "============================================="
echo "  Setup Complete! Launching Services...      "
echo "============================================="
echo "Start backend:  uvicorn main:app --reload (in backend/)"
echo "Start frontend: npm run dev (in dashboard/)"
echo "Run scenarios:  ./scripts/run-demo.sh"

