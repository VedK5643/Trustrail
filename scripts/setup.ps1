Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  TrustRail — Spend Governance Setup Script  " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# 1. Start Postgres DB via Docker
Write-Host "`n[1/5] Starting Postgres DB container..." -ForegroundColor Yellow
docker compose up -d db

# Wait for Postgres container ready
Write-Host "Waiting 5 seconds for Postgres to initialize..."
Start-Sleep -Seconds 5

# 2. Python environment & dependencies
Write-Host "`n[2/5] Installing backend dependencies..." -ForegroundColor Yellow
pip install -r backend/requirements.txt

# 3. Generate synthetic data & Train XGBoost
Write-Host "`n[3/5] Generating synthetic transactions & Training ML Risk Model..." -ForegroundColor Yellow
python data/synthetic_generator.py
python backend/ml/train.py

# 4. Seed Database
Write-Host "`n[4/5] Seeding database with historical agent & merchant data..." -ForegroundColor Yellow
python data/seed_db.py

# 5. Setup Agents & Dashboard
Write-Host "`n[5/5] Installing Agent & Dashboard Node dependencies..." -ForegroundColor Yellow
Set-Location agents
npm install
Set-Location ../dashboard
npm install
Set-Location ..

Write-Host "`n=============================================" -ForegroundColor Green
Write-Host "  Setup Complete! Launching Services...      " -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "Run 'docker compose up -d' or start backend and dashboard manually:"
Write-Host "  Backend:   uvicorn main:app --reload (in backend/)"
Write-Host "  Dashboard: npm run dev (in dashboard/)"
Write-Host "  Demo Run:  powershell scripts/run-demo.ps1"

