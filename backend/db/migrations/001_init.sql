-- TrustRail Postgres Schema Initial Migration
-- All timestamps TIMESTAMPTZ, monetary amounts NUMERIC(12,2)

CREATE TABLE IF NOT EXISTS raw_webhook_events (
    id SERIAL PRIMARY KEY,
    paypal_event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    trust_alpha NUMERIC(10,4) NOT NULL DEFAULT 1.0,
    trust_beta NUMERIC(10,4) NOT NULL DEFAULT 1.0,
    trust_score NUMERIC(5,4) NOT NULL DEFAULT 0.5,
    trust_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    paypal_order_id TEXT UNIQUE NOT NULL,
    paypal_auth_id TEXT,
    paypal_capture_id TEXT,
    agent_id TEXT NOT NULL REFERENCES agents(id),
    merchant_id TEXT NOT NULL,
    merchant_name TEXT NOT NULL,
    merchant_category TEXT NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    description TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    risk_score NUMERIC(5,4),
    risk_threshold NUMERIC(5,4),
    shap_explanation JSONB,
    policy_violations JSONB,
    decision TEXT,
    decision_reason TEXT,
    resolved_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    authorized_at TIMESTAMPTZ,
    decided_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS agent_rolling_stats (
    agent_id TEXT PRIMARY KEY REFERENCES agents(id),
    txn_count INTEGER NOT NULL DEFAULT 0,
    rolling_mean_amount NUMERIC(12,4) NOT NULL DEFAULT 0,
    rolling_std_amount NUMERIC(12,4) NOT NULL DEFAULT 1,
    txn_last_1h INTEGER NOT NULL DEFAULT 0,
    txn_last_24h INTEGER NOT NULL DEFAULT 0,
    avg_hour_of_day NUMERIC(5,2) NOT NULL DEFAULT 12.0,
    std_hour_of_day NUMERIC(5,2) NOT NULL DEFAULT 6.0,
    known_merchants JSONB NOT NULL DEFAULT '[]'::jsonb,
    known_categories JSONB NOT NULL DEFAULT '[]'::jsonb,
    daily_spend_today NUMERIC(12,2) NOT NULL DEFAULT 0,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS merchant_history (
    merchant_id TEXT PRIMARY KEY,
    merchant_name TEXT NOT NULL,
    category TEXT NOT NULL,
    txn_count INTEGER NOT NULL DEFAULT 0,
    avg_amount NUMERIC(12,4) NOT NULL DEFAULT 0,
    std_amount NUMERIC(12,4) NOT NULL DEFAULT 1,
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS policies (
    agent_id TEXT PRIMARY KEY REFERENCES agents(id),
    daily_spend_cap NUMERIC(12,2),
    per_txn_cap NUMERIC(12,2),
    merchant_allowlist JSONB NOT NULL DEFAULT '[]'::jsonb,
    merchant_denylist JSONB NOT NULL DEFAULT '[]'::jsonb,
    category_allowlist JSONB NOT NULL DEFAULT '[]'::jsonb,
    category_denylist JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_agent_id ON transactions(agent_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_paypal_order_id ON transactions(paypal_order_id);
CREATE INDEX IF NOT EXISTS idx_raw_webhook_events_event_type ON raw_webhook_events(event_type);

-- Seed initial agents and default policies
INSERT INTO agents (id, name, description, trust_alpha, trust_beta, trust_score)
VALUES 
    ('procurement-agent', 'Procurement Agent', 'Procures office supplies, hardware, and operational items', 1.0, 1.0, 0.5),
    ('subscription-agent', 'Subscription Agent', 'Manages cloud subscriptions, SaaS licenses, and recurring tools', 1.0, 1.0, 0.5),
    ('travel-agent', 'Travel Booking Agent', 'Books corporate travel, flights, rail, and hotels', 1.0, 1.0, 0.5)
ON CONFLICT (id) DO NOTHING;

INSERT INTO policies (agent_id, daily_spend_cap, per_txn_cap, category_denylist)
VALUES 
    ('procurement-agent', 2000.00, 500.00, '["gambling", "crypto", "electronics_gaming"]'::jsonb),
    ('subscription-agent', 1000.00, 200.00, '["gambling", "crypto"]'::jsonb),
    ('travel-agent', 7500.00, 3500.00, '["gambling", "crypto", "electronics_gaming"]'::jsonb)
ON CONFLICT (agent_id) DO NOTHING;

INSERT INTO agent_rolling_stats (agent_id)
VALUES 
    ('procurement-agent'),
    ('subscription-agent'),
    ('travel-agent')
ON CONFLICT (agent_id) DO NOTHING;

