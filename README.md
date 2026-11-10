# TrustRail — Explainable PayPal Spend Governance for AI Agents

**TrustRail** is an explainable spend-governance and reputation firewall for autonomous AI agents transacting through PayPal. Instead of blindly capturing payments, TrustRail enforces PayPal's `intent=AUTHORIZE` flow so every agent-initiated purchase is authorized first and gated on **Policy-as-Code rules**, an **XGBoost anomaly detector with SHAP & counterfactual explanations**, and a **velocity-aware Beta-distribution Trust Score** before funds are ever captured or voided.

---

## Architecture & How It Works

1. **Authorize-First PayPal Flow (`intent=AUTHORIZE`)**: Agents create real PayPal Sandbox orders (`payment_source.paypal`), pause for buyer authorization approval, acquire a real PayPal Authorization ID, and submit the authorized transaction to TrustRail (`/api/evaluate`) — never using mock tokens or fake fallback orders.
2. **Dual Policy + ML Evaluation**:
   - **Policy-as-Code** (`backend/services/policy_engine.py`): Enforces per-agent spend limits (`per_txn_cap`, `daily_spend_cap`) and merchant/category allowlists & denylists (e.g., Procurement `$500/txn`, Subscription `$200/txn`, Travel Booking `$3,500/txn` & `$7,500/day`).
   - **11-Feature ML Risk Model + SHAP** (`backend/services/feature_engine.py`, `risk_scorer.py`, `shap_explainer.py`): Always scores every transaction (even if policy blocks) across 11 behavioral features including `amount_zscore`, `amount_merchant_zscore`, `velocity_1h`, `velocity_24h`, `same_merchant_txn_1h`, novelty, hour deviation, daily spend ratio, and `log_amount`, returning plain-English SHAP drivers and counterfactuals.
3. **Beta-Distribution Trust Engine** (`backend/services/trust_score.py`):
   - Adapts effective risk thresholds within `[base - 0.15, base + 0.15]` using time-decayed $\alpha / (\alpha + \beta)$ scores.
   - Freezes trust growth during elevated bursts (`same_merchant_txn_1h > 1` or `velocity_1h > 3`) so runaway loops cannot boost their own thresholds, awards `+0.5` $\alpha$ after human vindication (`APPROVED`), and penalizes `POLICY_BLOCK` (`+1.0` $\beta$) and `DENIED` (`+2.0` $\beta$).
4. **Live Compliance Dashboard** (`dashboard/`): Apple-styled dark & light mode React dashboard displaying real-time transactions, risk capsules, inline SHAP cards, trust gauges, human Approve/Deny PayPal capture/void actions, and a Policy-as-Code editor.

---

## Prerequisites

- **Python 3.11+** (recommended 3.11 or 3.12)
- **Node.js 20+** and **npm**
- **PayPal Developer Account & Sandbox App**:
  1. Log in to the [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/).
  2. Under **Apps & Credentials (Sandbox)**, create or open a REST API app and copy its **Client ID** and **Client Secret**.
  3. Under **Testing Tools -> Sandbox Accounts**, locate your **US Personal buyer sandbox account** (email & password).
     > **Why a US Personal buyer account is required:** All order payloads use `USD` because PayPal's Orders v2 API returns `422 CURRENCY_NOT_SUPPORTED` for domestic `INR` orders. If your sandbox personal buyer account is non-US (for example, `IN`) or mismatched in currency, PayPal's checkout UI rejects payment at the currency step. Logging in with a **US** Personal Sandbox buyer account works cleanly with any sandbox business merchant app.
- *(Optional)* **Docker / PostgreSQL 16** if running Postgres instead of the default local SQLite database.

---

## Step 1: Environment Configuration

Copy `.env.example` to `.env` in the repository root and fill in your real PayPal Sandbox credentials:

```bash
cp .env.example .env
```

Edit `.env`:
- **`PAYPAL_CLIENT_ID`**: Your Sandbox REST app Client ID (**required** — app raises an error if left placeholder).
- **`PAYPAL_CLIENT_SECRET`**: Your Sandbox REST app Client Secret (**required**).
- **`PAYPAL_SANDBOX_BUYER_EMAIL`**: Your US Personal Sandbox buyer email (printed in terminal prompts as a login reminder).
- **`DATABASE_URL`**: Leave **unset** for zero-config local SQLite (defaults automatically to the unified `backend/trustrail.db` path regardless of working directory), or set an absolute SQLite URI / PostgreSQL URI (`postgresql+asyncpg://...`).
- **`OPENAI_API_KEY`**: *(Optional)* Set to use OpenAI (`gpt-4o-mini`) for agent purchase formulation; otherwise deterministic structured reasoning runs automatically.

---

## Step 2: Install Dependencies

Install backend Python dependencies (includes `aiosqlite`, `xgboost`, `shap`, `fastapi`, `uvicorn`, `httpx`):

```bash
pip install -r backend/requirements.txt
```

Install Node dependencies for the AI agent scenarios and React dashboard:

```bash
npm install --prefix agents
npm install --prefix dashboard
```

---

## Step 3: Generate Data, Train ML Model & Seed Database

Run these three commands **in order** from the repository root:

```bash
# 1. Generate 6,300 synthetic historical baseline & anomaly transactions
python data/synthetic_generator.py

# 2. Train the 11-feature XGBoost model and compute the optimal threshold
python backend/ml/train.py

# 3. Initialize schema, seed baseline agents (trust = 0.50), policies & history
python data/seed_db.py
```

Verify your PayPal Sandbox OAuth2 & Orders API connectivity before running demos:

```bash
python scripts/verify_paypal.py
```

---

## Step 4: Start the Backend & Dashboard

Open **two terminals** at the repository root:

**Terminal 1 — FastAPI Governance Backend (`http://localhost:8000`):**
```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
Verify health at `http://127.0.0.1:8000/health` (`{"status":"healthy",...}`).

**Terminal 2 — React Compliance Dashboard (`http://localhost:5173`):**
```bash
npm run dev --prefix dashboard
```
Open **`http://localhost:5173`** in your browser (use the **Light / Dark** button in the top-right header to toggle themes).

---

## Step 5: Run the 3 End-to-End Demo Scenarios

Run each scenario from a **third terminal** at the repository root.

> **Important — Manual PayPal Sandbox Approval Step:**  
> Because standard PayPal Wallet Checkout (`payment_source.paypal`) returns `PAYER_ACTION_REQUIRED`, every scenario pauses in the terminal and prints a real `https://www.sandbox.paypal.com/checkoutnow?token=...` URL. For each transaction:
> 1. Open the printed link in your browser.
> 2. Log in with your **US Personal Sandbox buyer** account.
> 3. Click **Pay Now / Complete Purchase**.
> 4. Return to the terminal and press **`Enter`** to acquire the PayPal Authorization ID and submit to TrustRail.

### Scenario A — Rogue Prompt-Injection Purchase (`POLICY_BLOCK` -> Immediate `VOIDED`)
```bash
npm run scenario:a --prefix agents
```
- **What happens**: Prompt injection instructs `procurement-agent` to buy a **$4,500.00** gaming laptop from `NewVendor-Gaming` (`electronics_gaming`).
- **Expected outcome**:
  - After browser approval & authorization, TrustRail evaluates **both** policy and the ML model.
  - Triggers policy violations (`per_txn_cap`, `daily_spend_cap`, `category_denylist`) **and** ~99.9%+ ML risk with SHAP explanations.
  - TrustRail immediately **VOIDs** the authorization on PayPal Sandbox (`status = VOIDED`, `decision = POLICY_BLOCK`) — zero funds captured.

### Scenario B — Runaway Duplicate Subscription Loop (`same_merchant_txn_1h` Detection -> `HELD`)
```bash
npm run scenario:b --prefix agents
```
- **What happens**: Simulates a billing retry bug on `subscription-agent` firing 3 rapid **$29.00** Slack renewals (`merch_saas_01`). Complete browser approval for each iteration when prompted.
- **Expected outcome**:
  - **Iteration 1**: Baseline charge (`same_merchant_txn_1h = 1`) -> `AUTO_CAPTURED`.
  - **Iteration 2**: Elevated burst detected (`same_merchant_txn_1h = 2`); trust growth is **frozen** (`+0.0`) so threshold does not climb -> clears or nears threshold (`AUTO_CAPTURED` / `HELD` depending on prior baseline).
  - **Iteration 3**: `same_merchant_txn_1h = 3` spikes risk above the frozen dynamic threshold -> **`HELD`** with SHAP driver (`"3 duplicate charges to Slack Technologies within the last hour"`) and counterfactual insight.

### Scenario C — Legitimate Large Purchase (`HELD` -> Human Approval -> `CAPTURED`)
```bash
npm run scenario:c --prefix agents
```
- **What happens**: `travel-agent` books a legitimate **$2,800.00** executive flight (`SFO -> LHR`) on `Delta Air Lines` (~7–8x the agent's $379 average).
- **Expected outcome**:
  1. Complete the PayPal Sandbox browser approval step and press `Enter`.
  2. Passes Travel Agent policy limits (`per_txn_cap = $3,500`, `daily_spend_cap = $7,500`).
  3. XGBoost flags the unusual amount (~99.9% risk) -> transaction lands on **`HELD`** (`HOLD`).
  4. **Dashboard Human-in-the-Loop Approval**:
     - Open **`http://localhost:5173`**, expand the held **Delta Air Lines** row, review its SHAP explanation & counterfactual, and click **Approve & Capture**.
     - TrustRail captures the authorization on PayPal Sandbox (`status = CAPTURED`, real `paypal_capture_id`), and `travel-agent`'s Trust Score increases (`alpha += 0.5`).

*(Optional helper scripts `scripts/run-demo.ps1` and `scripts/run-demo.sh` walk through Scenarios A, B, and C sequentially.)*

---

## Stretch / Optional Features *(Not Wired into Core Demo)*

These modules are included in the repository as architectural extensions and are **not** required or executed during Scenarios A–C:
- **Customer Disputes Feedback (`agents/scenarios/scenario-d-dispute.ts`, `backend/routers/disputes.py`)**: Queries PayPal's `/v1/customer/disputes` API and feeds dispute resolutions into TrustRail's Beta reputation model; falls back to sample ID `PP-D-10293` when a fresh sandbox merchant has zero active disputes.
- **PayPal Webhooks Receiver (`backend/routers/webhooks.py`)**: Implements `/webhooks/paypal` signature verification via PayPal's `/v1/notifications/verify-webhook-signature` endpoint; requires a publicly reachable HTTPS webhook URL and an active `PAYPAL_WEBHOOK_ID`.

---

## Directory Structure

- `agents/`: TypeScript PayPal Checkout client (`src/common/paypal-client.ts`), terminal buyer-approval helper, LLM client, 3 autonomous agents, and demo scenarios (`scenarios/`).
- `backend/`: FastAPI service (`main.py`), SQLAlchemy ORM & Postgres migration (`db/`), policy engine, 11-feature engineering, XGBoost inference & training (`ml/`), SHAP + counterfactual explainer, Beta trust scoring, and PayPal REST client (`services/`).
- `dashboard/`: React 18 + Vite + Tailwind UI with Apple dark & light modes, live transaction feed, SHAP inspector, trust score cards, and Policy-as-Code editor.
- `data/`: Synthetic transaction generator (`synthetic_generator.py`), merchant catalog (`merchants.json`), and idempotent database seeder (`seed_db.py`).
- `scripts/`: PayPal connectivity verifier (`verify_paypal.py`), setup scripts, and interactive demo runner scripts.

---

## License

Licensed under the [MIT License](LICENSE).
