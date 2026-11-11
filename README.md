# TrustRail

> **Explainable pre-capture spend-governance firewall for AI agents integrated with PayPal Sandbox.**

Live Hosted Dashboard: [https://trustrail-gamma.vercel.app/](https://trustrail-gamma.vercel.app/)  
Hosted API Health Check: [https://trustreail-backend.onrender.com/health](https://trustreail-backend.onrender.com/health)

---

## Problem Statement

Autonomous AI agents given payment credentials create three immediate operational hazards:

1. **Prompt-injection & rogue purchases** — compromised or manipulated agents attempt out-of-policy, high-value purchases (such as unauthorized hardware).
2. **Runaway retry & subscription loops** — malfunctioning agents repeatedly charge the same merchant in tight bursts before humans notice.
3. **Opaque, all-or-nothing execution** — traditional payment flows settle funds immediately without real-time behavioral risk scoring, human-in-the-loop review for borderline high-value orders, or clear explanations of *why* a payment was flagged.

## Solution Overview

**TrustRail** acts as a pre-capture spend-governance firewall between autonomous TypeScript purchasing agents and **PayPal Sandbox** settlement. Every transaction uses PayPal's `intent=AUTHORIZE` Orders v2 flow so funds are authorized first and routed through TrustRail's FastAPI governance engine (`POST /api/evaluate`) **before** any money is captured:

- **Policy-as-Code** blocks hard violations immediately (`POLICY_BLOCK` -> PayPal authorization `VOIDED`).
- **11-Feature XGBoost Risk Scoring** evaluates behavioral velocity, merchant/category novelty, spending ratios, and timing anomalies against a calibrated decision threshold (`0.5091`).
- **Beta-Distribution Agent Trust Engine** tightens or relaxes each agent's effective risk threshold dynamically based on past outcomes, hourly time decay, and burst-velocity protection.
- **SHAP Explanations & Counterfactuals** reveal the top-3 risk drivers and minimal threshold-clearing adjustments so operators can approve or deny held orders confidently from the React dashboard.

---

## Key Features

- **Pre-Capture PayPal Authorization Gate**: Creates genuine PayPal Sandbox Orders (`intent=AUTHORIZE`), enforces human Sandbox checkout approval (`PAYER_ACTION_REQUIRED`), evaluates risk prior to capture, and executes real PayPal Capture or Void calls.
- **Configurable Policy-as-Code**: Enforces per-transaction caps, daily spend caps, merchant denylists, category denylists, and allowlists per agent, editable live via the dashboard or REST API (`PUT /policies/{agent_id}`).
- **Calibrated ML Risk Scorer**: Trains an XGBoost classifier on 11 behavioral and contextual features (`ROC-AUC: 0.9832`, calibrated threshold `0.5091`).
- **Explainable Decisions (SHAP + Counterfactuals)**: Computes per-transaction `shap.TreeExplainer` attributions and 20-step binary-search counterfactuals (with heuristic fallback when no tree explainer is loaded).
- **Velocity-Aware Beta Trust Scoring**: Tracks agent reputation via Beta `(alpha, beta)` parameters with hourly decay (`0.999 ** hours_since`), adaptive thresholds, and automatic reward freezing during high-velocity bursts.
- **Multi-Provider LLM Support**: Supports Google Gemini (`GEMINI_API_KEY`, defaulting to `gemini-2.5-flash` via Gemini's OpenAI-compatible endpoint) with automatic fallback to OpenAI (`OPENAI_API_KEY`, `gpt-4o-mini`) or deterministic offline payloads.
- **Human-in-the-Loop Dashboard**: React + Vite interface with real-time polling (`5s`), agent trust scorecards, live risk badges, SHAP breakdowns, policy editor, and one-click **Approve & Capture** / **Deny & Void** controls.

---

## Three Core Demo Scenarios

TrustRail demonstrates three end-to-end governance outcomes against PayPal Sandbox:

| Scenario | Agent | Trigger / Purchase | Governance Outcome | Final Settlement Status |
| :--- | :--- | :--- | :--- | :--- |
| **A — Rogue Agent** (`npm run scenario:a`) | `procurement-agent` | Prompt-injected `$4,500` gaming laptop purchase | Blocked by Policy-as-Code / risk controls (`POLICY_BLOCK`) | `VOIDED` |
| **B — Runaway Agent** (`npm run scenario:b`) | `subscription-agent` | Repeated `$29` Slack subscription charges (`SCENARIO_B_ITERATIONS=3`) | Repeated merchant velocity freeze triggers review (`HOLD`) | Iteration 3 `HELD` |
| **C — Human Approval** (`npm run scenario:c`) | `travel-agent` | Legitimate `$2,800` San Francisco-to-London (`SFO -> LHR`) Delta flight | Held for human review (`HOLD`) -> approved in dashboard | `CAPTURED` |

> **Optional Stretch Scenario**: [scenario-d-dispute.ts](agents/scenarios/scenario-d-dispute.ts) and the `/disputes` / `/webhooks/paypal` endpoints are included as optional stretch prototypes and are not required for Scenarios A–C.

---

## Architecture Overview

```mermaid
flowchart LR
    Agent["TypeScript AI Agents (Gemini or OpenAI)"] -->|"1. Create Order (intent=AUTHORIZE)"| PayPal["PayPal Sandbox Orders v2"]
    Browser["Human Buyer Browser Checkout"] -->|"2. Approve Sandbox Order"| PayPal
    Agent -->|"3. Authorize and POST /api/evaluate"| API["FastAPI Governance Engine (Render)"]
    API --> Policy["Policy-as-Code Engine"]
    API --> ML["11-Feature XGBoost + SHAP + Beta Trust"]
    API <--> DB["Supabase PostgreSQL or Local SQLite"]
    API -->|"AUTO_CLEAR Capture or POLICY_BLOCK Void"| PayPal
    Dashboard["React + Vite Dashboard (Vercel)"] <-->|"Poll /agents, /transactions, PUT /policies"| API
    Dashboard -->|"Approve and Capture / Deny and Void"| API
```

### System Workflow

1. **Purchase Generation**: A TypeScript agent (`procurement-agent`, `subscription-agent`, or `travel-agent`) builds a structured purchase intent via Gemini, OpenAI, or scenario demo payloads.
2. **Order Creation & Human Checkout**: The agent calls PayPal Sandbox Orders v2 with `intent: "AUTHORIZE"` and redirects `return_url` / `cancel_url` to `https://trustrail-gamma.vercel.app/`. Execution pauses while a human buyer approves the Sandbox checkout in the browser (`PAYER_ACTION_REQUIRED`).
3. **Authorization & Evaluation**: After browser approval, the agent authorizes the PayPal order and sends the transaction payload and PayPal IDs to `POST /api/evaluate`.
4. **Policy Check**: The Policy-as-Code engine evaluates spend caps and allow/denylists. Hard violations immediately void the PayPal authorization (`POLICY_BLOCK` -> `VOIDED`) and decrease agent trust (`beta += 1.0`).
5. **Risk, Explainability & Adaptive Thresholding**: The feature engine computes 11 context/velocity features, XGBoost produces a risk probability, `shap.TreeExplainer` generates top-3 drivers and a counterfactual, and the Beta trust engine calculates `effective_threshold = clamp(base_threshold + (trust_score - 0.5) * 0.3, 0.1, 0.95)`.
6. **Settlement or Human Review**:
   - **Below threshold** -> auto-captured via PayPal Capture (`AUTO_CAPTURED`), updating trust (`alpha += 0.05`, or frozen at `+0.0` if `same_merch_v1h > 1` or `v1h > 3`).
   - **At or above threshold** -> held (`HELD`) for human decision in the Vercel/local dashboard. Clicking **Approve & Capture** executes PayPal Capture (`CAPTURED`, `alpha += 0.5`); clicking **Deny & Void** executes PayPal Void (`VOIDED`, `beta += 2.0`).

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **AI Agents & LLM Client** | TypeScript (`tsx`), Google Gemini (`gemini-2.5-flash` via OpenAI-compatible API), OpenAI (`gpt-4o-mini`) fallback |
| **Payment Rail** | PayPal Sandbox REST API (OAuth2, Orders v2 `intent=AUTHORIZE`, Authorizations Capture & Void) |
| **Backend API** | Python 3.11, FastAPI, Uvicorn, SQLAlchemy Async (`greenlet`, `asyncpg`, `aiosqlite`), Pydantic / `pydantic-settings`, `httpx` |
| **ML & Explainability** | XGBoost (`model.json`, `threshold.json`), SHAP (`TreeExplainer`), scikit-learn, pandas, numpy, Beta-distribution trust engine |
| **Database** | Supabase PostgreSQL (deployed via IPv4 Session Pooler port `5432`) / SQLite (`backend/trustrail.db` default local fallback) |
| **Frontend Dashboard** | React, TypeScript, Vite, Tailwind CSS |
| **Hosting & Tooling** | Render (FastAPI backend), Vercel (React dashboard), Docker Compose (`docker-compose.yml`) |

---

## How PayPal Sandbox Is Integrated

- **Sandbox-Only Rail**: TrustRail targets `https://api-m.sandbox.paypal.com` exclusively—never production credentials or real-money processing.
- **Authorize-First Lifecycle**: Orders in [paypal-client.ts](agents/src/common/paypal-client.ts) and [paypal_service.py](backend/services/paypal_service.py) always set `intent: "AUTHORIZE"`, ensuring PayPal reserves funds without settlement until TrustRail clears or a human approves the order.
- **Genuine Buyer Approval**: Orders return a `PAYER_ACTION_REQUIRED` approval URL that requires logging into a PayPal Sandbox buyer account in a browser before authorization succeeds.
- **Redirect Target**: Both `return_url` and `cancel_url` point to the hosted dashboard root (`https://trustrail-gamma.vercel.app/`), avoiding dead local hosts while the terminal script prompts to continue authorization.

---

## How AI & LLM Options Are Integrated

### 1. Pre-Capture ML, Explainability & Trust

- **11 Engineered Features** ([feature_engine.py](backend/services/feature_engine.py)):
  `amount_zscore`, `amount_merchant_zscore`, `velocity_1h`, `velocity_24h`, `same_merchant_txn_1h`, `merchant_novelty`, `category_novelty`, `hour_of_day`, `hour_deviation`, `daily_spend_ratio`, and `log_amount`.
- **Calibrated XGBoost Model** ([model.json](backend/ml/model.json), [threshold.json](backend/ml/threshold.json)):
  Trained on `6,300` synthetic transactions across `48` merchants ([merchants.json](data/merchants.json), [synthetic_generator.py](data/synthetic_generator.py)), recording `ROC-AUC = 0.9832` with base threshold `0.5091`.
- **SHAP & Counterfactuals** ([shap_explainer.py](backend/services/shap_explainer.py)):
  Uses `shap.TreeExplainer` to surface the top 3 positive risk contributors and runs a 20-step binary-search counterfactual over the top feature (falling back to heuristics if `explainer is None`).
- **Beta-Distribution Trust Engine** ([trust_score.py](backend/services/trust_score.py)):
  Applies `0.999 ** hours_since` exponential time decay in memory on read-only `/agents` calls and persists `alpha`/`beta` updates only on real outcomes (`AUTO_CAPTURED`: `+0.05` alpha frozen under burst velocity, `APPROVED`: `+0.5` alpha, `POLICY_BLOCK`: `+1.0` beta, `DENIED`: `+2.0` beta; optional disputes: `+3.0` beta / `+1.0` alpha).
- **Default Policy Profiles** ([policy_engine.py](backend/services/policy_engine.py)):
  - `procurement-agent`: `$500` per-txn cap, `$2,000` daily cap, `merchant_denylist: ["newvendor-gaming"]`, `category_denylist: ["gambling", "crypto", "electronics_gaming"]`
  - `subscription-agent`: `$200` per-txn cap, `$1,000` daily cap
  - `travel-agent`: `$3,500` per-txn cap, `$7,500` daily cap

### 2. Agent LLM Configuration (Gemini & OpenAI)

[llm-client.ts](agents/src/common/llm-client.ts) resolves LLM credentials in priority order:

1. **Google Gemini (Recommended / Checked First)**:
   Set `GEMINI_API_KEY` in `.env`. The client targets Gemini's OpenAI-compatible endpoint (`https://generativelanguage.googleapis.com/v1beta/openai/`) and defaults `LLM_MODEL` to `gemini-2.5-flash`.
2. **OpenAI (Automatic Fallback)**:
   If `GEMINI_API_KEY` is unset, the client checks `OPENAI_API_KEY` and defaults `LLM_MODEL` to `gpt-4o-mini` (or honors a custom `LLM_BASE_URL`).
3. **Offline Deterministic Fallback**:
   If neither API key is set, agents fall back cleanly to their structured `defaultPurchase` payload. *(Demo scripts `scenario-a/b/c` also apply `overridePurchase` values so hackathon runs remain reproducible regardless of LLM variance.)*

---

## Deployment Information & Hosted Demo

| Component | Platform | URL / Runtime Role |
| :--- | :--- | :--- |
| **Dashboard UI** | Vercel (React + Vite) | [https://trustrail-gamma.vercel.app/](https://trustrail-gamma.vercel.app/) |
| **Governance API** | Render (FastAPI) | [https://trustreail-backend.onrender.com](https://trustreail-backend.onrender.com) |
| **Database** | Supabase PostgreSQL | Session Pooler (port `5432`, IPv4 + `asyncpg`) |
| **Scenario Agents** | Local Workstation (`tsx`) | Runs Scenarios A, B, C against `BACKEND_URL` and PayPal Sandbox |

To drive the live hosted stack from your machine during a demo, set `BACKEND_URL=https://trustreail-backend.onrender.com` in your local `.env`, execute `npm run scenario:a`, `scenario:b`, or `scenario:c`, and observe live updates on [https://trustrail-gamma.vercel.app/](https://trustrail-gamma.vercel.app/).

---

## API Endpoint Summary

| Method & Path | Purpose | Router |
| :--- | :--- | :--- |
| `GET /health` | Health check and service version metadata | [health.py](backend/routers/health.py) |
| `POST /api/evaluate` | Evaluate PayPal-authorized order (policy, 11 features, XGBoost, SHAP, Beta trust -> `AUTO_CAPTURED`, `VOIDED`, or `HELD`) | [transactions.py](backend/routers/transactions.py) |
| `GET /transactions` | List evaluated transactions (`limit` 1–200 default 50, optional `agent_id` & `status` filters) | [transactions.py](backend/routers/transactions.py) |
| `GET /agents` | Read-only agent trust & rolling-stats summary with in-memory time decay | [agents.py](backend/routers/agents.py) |
| `POST /decisions/{txn_id}/approve` | Human-approve a `HELD` transaction -> PayPal Capture (`CAPTURED`, `alpha += 0.5`) | [decisions.py](backend/routers/decisions.py) |
| `POST /decisions/{txn_id}/deny` | Human-deny a `HELD` transaction -> PayPal Void (`VOIDED`, `beta += 2.0`) | [decisions.py](backend/routers/decisions.py) |
| `GET /policies/{agent_id}` | Retrieve spend caps and allow/denylists for an agent | [policies.py](backend/routers/policies.py) |
| `PUT /policies/{agent_id}` | Create or update an agent's spend policy rules | [policies.py](backend/routers/policies.py) |
| `GET /disputes`, `POST /disputes/{dispute_id}/resolve` | *Optional stretch*: inspect and resolve dispute prototypes | [disputes.py](backend/routers/disputes.py) |
| `POST /webhooks/paypal` | *Optional stretch*: handle PayPal Sandbox dispute webhook events | [webhooks.py](backend/routers/webhooks.py) |

---

## Project Structure

```text
.
├── .env.example                       # Placeholder environment template
├── .gitignore
├── LICENSE                            # MIT License
├── README.md
├── docker-compose.yml                 # Local Postgres, FastAPI backend, and dashboard containers
├── agents/
│   ├── package.json                   # Agent & scenario npm scripts
│   ├── tsconfig.json
│   ├── scenarios/
│   │   ├── scenario-a-rogue.ts        # Prompt-injected $4,500 gaming laptop -> POLICY_BLOCK / VOIDED
│   │   ├── scenario-b-velocity.ts     # Repeated $29 Slack charges -> HELD on Iteration 3
│   │   ├── scenario-c-legitimate.ts   # $2,800 SFO->LHR Delta flight -> HELD -> human CAPTURED
│   │   └── scenario-d-dispute.ts      # Optional stretch dispute scenario
│   └── src/
│       ├── procurement-agent.ts
│       ├── subscription-agent.ts
│       ├── travel-agent.ts
│       └── common/
│           ├── approval-prompt.ts
│           ├── llm-client.ts          # GEMINI_API_KEY first, OPENAI_API_KEY fallback
│           ├── paypal-client.ts       # PayPal Sandbox Orders v2 client
│           └── types.ts
├── backend/
│   ├── Dockerfile
│   ├── config.py                      # Pydantic settings & paths
│   ├── main.py                        # FastAPI entrypoint, CORS, routers
│   ├── requirements.txt
│   ├── db/
│   │   ├── engine.py                  # Async SQLAlchemy engine (Postgres / SQLite)
│   │   ├── models.py                  # ORM schema (agents, transactions, policies, etc.)
│   │   └── migrations/001_init.sql    # PostgreSQL schema initialization
│   ├── ml/
│   │   ├── model.json                 # Trained XGBoost model
│   │   ├── threshold.json             # Calibrated threshold (0.5091) & ROC-AUC (0.9832)
│   │   └── train.py
│   ├── routers/                       # FastAPI endpoints (health, transactions, decisions, agents, policies, disputes, webhooks)
│   └── services/                      # Orchestrator, policy engine, feature engine, XGBoost, SHAP, Beta trust, PayPal client
├── dashboard/
│   ├── Dockerfile
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── types.ts
│       ├── api/client.ts
│       ├── hooks/usePolling.ts        # 5s polling loop with in-flight guard
│       └── components/                # AgentSidebar, TrustScoreCard, TransactionFeed, TransactionRow, RiskBadge, ShapExplanation, ApproveButton, DenyButton, PolicyEditor
├── data/
│   ├── merchants.json                 # 48 merchant profiles
│   ├── seed_db.py                     # Database seeder
│   ├── synthetic_generator.py         # Generates 6,300 synthetic training records
│   └── generated/synthetic_transactions.csv
└── scripts/
    ├── run-demo.ps1 / run-demo.sh
    ├── setup.ps1 / setup.sh
    └── verify_paypal.py
```

---

## Prerequisites

- **Node.js** (20 recommended; container uses `node:20-alpine`) and **npm**
- **Python** (3.11 recommended; container uses `python:3.11-slim`) and **pip**
- **PayPal Developer Account** with a Sandbox REST application (`PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET`)
- **US Personal PayPal Sandbox Buyer Account** (`PAYPAL_SANDBOX_BUYER_EMAIL`) for browser checkout approval in USD
- **Optional LLM Key**: Google `GEMINI_API_KEY` (recommended) or `OPENAI_API_KEY`
- **Optional Docker**: Required only if using [docker-compose.yml](docker-compose.yml) or the Docker-based setup helpers in `scripts/`

---

## Setup & Installation

### 1. Clone and Configure Environment Variables

```bash
git clone https://github.com/VedK5643/Trustrail.git
cd Trustrail
cp .env.example .env
```

Edit `.env` with your PayPal Sandbox credentials and preferred LLM key (never commit `.env`). Reference of all variables in [.env.example](.env.example):

| Variable | Example / Default Placeholder | Component & Description |
| :--- | :--- | :--- |
| `PAYPAL_CLIENT_ID` | `sandbox_client_id_placeholder` | PayPal Sandbox REST App Client ID (Agents & Backend) |
| `PAYPAL_CLIENT_SECRET` | `sandbox_client_secret_placeholder` | PayPal Sandbox REST App Client Secret (Agents & Backend) |
| `PAYPAL_SANDBOX_BASE_URL` | `https://api-m.sandbox.paypal.com` | PayPal Sandbox API base URL |
| `PAYPAL_SANDBOX_BUYER_EMAIL` | `sb-buyer@personal.example.com` | Sandbox Personal buyer email used for checkout logs/prompts |
| `PAYPAL_WEBHOOK_ID` | `sandbox_webhook_id_placeholder` | Optional stretch PayPal webhook verification ID |
| `DATABASE_URL` | *Commented out -> local SQLite* (`postgresql+asyncpg://trustrail:trustrail@localhost:5432/trustrail`) | Async DB URL; leaving unset defaults local backend to SQLite (`backend/trustrail.db`) |
| `GEMINI_API_KEY` | `your_gemini_api_key_here` | Primary LLM key (checked first by agents) |
| `LLM_MODEL` | `gemini-2.5-flash` | Model name (defaults to `gemini-2.5-flash` for Gemini or `gpt-4o-mini` for OpenAI) |
| `OPENAI_API_KEY` | *Commented out* (`your_llm_api_key_here`) | Fallback LLM key used when `GEMINI_API_KEY` is unset |
| `LLM_BASE_URL` | *Commented out* (`https://generativelanguage.googleapis.com/v1beta/openai/`) | Optional OpenAI-compatible base URL override |
| `BACKEND_URL` | `http://localhost:8000` | Target FastAPI governance backend URL for local agents (use `https://trustreail-backend.onrender.com` for hosted demo) |
| `RISK_MODEL_PATH` | `./ml/model.json` | Relative path to XGBoost model from `backend/` |
| `RISK_THRESHOLD_PATH` | `./ml/threshold.json` | Relative path to calibrated threshold JSON from `backend/` |
| `SCENARIO_B_ITERATIONS` | `3` | Number of charge iterations executed in Scenario B |
| `VITE_API_BASE_URL` | `http://localhost:8000` | API base URL compiled into the Vite React dashboard |

### 2. Backend Setup & Run (Local)

Install Python dependencies and start FastAPI from `backend/` (so `./ml/model.json` and `./ml/threshold.json` resolve cleanly):

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- When `DATABASE_URL` is unset in `.env`, the backend initializes local SQLite (`backend/trustrail.db`) automatically.
- For standalone PayPal Sandbox verification helpers, see [verify_paypal.py](scripts/verify_paypal.py).
- To run the full container stack with local PostgreSQL instead, see [docker-compose.yml](docker-compose.yml) (or `scripts/setup.ps1` / `scripts/setup.sh`, which target Docker PostgreSQL).

### 3. Frontend Dashboard Setup & Run (Local)

In a second terminal:

```bash
cd dashboard
npm install
npm run dev
```

Build check for production deployment:

```bash
npm run build
```

### 4. Agent & Demo Scenario Execution

In a third terminal, install agent dependencies:

```bash
cd agents
npm install
```

Run any of the three core scenarios:

```bash
# Scenario A: Rogue agent ($4,500 gaming laptop -> POLICY_BLOCK / VOIDED)
npm run scenario:a

# Scenario B: Runaway agent (repeated $29 Slack charges -> HELD on Iteration 3)
npm run scenario:b

# Scenario C: Human approval ($2,800 SFO->LHR Delta flight -> HELD -> human Approve & Capture)
npm run scenario:c
```

**During each scenario run**:
1. The script prints a PayPal Sandbox checkout approval link and pauses.
2. Open the approval URL in your browser (use a fresh **Incognito/Private** window if switching sessions; see Known Limitations below) and log in with your **US Personal Sandbox buyer** account to approve the order.
3. Return to the terminal and press **Enter** to continue authorization and governance evaluation.
4. For **Scenario C**, open the dashboard (local or [https://trustrail-gamma.vercel.app/](https://trustrail-gamma.vercel.app/)), inspect the `HELD` Delta Air Lines transaction and its SHAP drivers, and click **Approve & Capture** to settle funds (`CAPTURED`).

---

## Security Notes

- **Sandbox-Only Payment Integration**: TrustRail uses PayPal Sandbox endpoints exclusively and requires explicit browser buyer approval (`PAYER_ACTION_REQUIRED`) plus pre-capture authorization before any capture occurs.
- **Secret Hygiene**: `.env`, SQLite `*.db` files, and `node_modules` are excluded via `.gitignore`. Keep credentials only in environment variables or platform secret managers (Render, Vercel).
- **Hackathon Prototype Exposure Notice**: [main.py](backend/main.py) currently enables permissive CORS (`allow_origins=["*"]`, `allow_credentials=True`) and exposes governance read/mutation endpoints (`/decisions/*`, `/policies/*`, `/transactions`, `/agents`) without end-user authentication or RBAC. Add authentication middleware and restrict CORS origins before deploying outside a controlled demo environment.

---

## Known Limitations

- **PayPal Sandbox USD & Cross-Border Session Decline**: PayPal Sandbox orders execute in `USD` and require a **US Personal Sandbox buyer** account (`IN` domestic INR orders fail with `CURRENCY_NOT_SUPPORTED`). Reusing an authenticated `sandbox.paypal.com` cookie session across consecutive cross-border (`IN` business app <-> `US` buyer) checkouts can trigger PayPal Sandbox's automated decline (*"To comply with international regulations, this transaction has been declined."*). Signing out at `https://www.sandbox.paypal.com/signout`, opening a fresh Incognito window per checkout, or using a US Business sandbox app avoids this decline.
- **Manual Browser Checkout Step**: PayPal Sandbox wallet approval cannot be bypassed cleanly from headless scripts, so Scenarios A–C pause for manual buyer sign-in and approval in a browser.
- **Deterministic Scenario Payloads**: `scenario-a-rogue.ts`, `scenario-b-velocity.ts`, and `scenario-c-legitimate.ts` apply `overridePurchase` values over LLM output so demo pricing and merchants remain repeatable across runs.
- **Render Free-Tier Cold Starts**: On the hosted Render deployment, inactivity (>15 minutes) puts the FastAPI instance to sleep, adding ~30–60s latency to the first wake-up request.
- **Windows Agent Entrypoint Quirk**: Running `npm run procurement`, `npm run subscription`, or `npm run travel` directly on Windows fails the `import.meta.url === file://${process.argv[1]}` guard; always run `npm run scenario:a`, `npm run scenario:b`, and `npm run scenario:c`.
- **Docker Assumptions in Helper Scripts**: [setup.ps1](scripts/setup.ps1) and [setup.sh](scripts/setup.sh) assume Docker PostgreSQL, whereas leaving `DATABASE_URL` unset in `.env` uses local SQLite.
- **Prototype Scope**: Synthetic training data (`data/synthetic_transactions.csv`) powers the initial model; `dashboard/package.json` includes an unused `recharts` dependency; and `/webhooks/paypal` plus `scenario-d-dispute.ts` are stretch extensions outside the core three-scenario flow.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for full details.
