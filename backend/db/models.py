from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Text, ForeignKey, func, JSON
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from db.engine import Base

JsonType = JSON().with_variant(JSONB, "postgresql")

class RawWebhookEvent(Base):
    __tablename__ = "raw_webhook_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paypal_event_id = Column(Text, unique=True, nullable=False)
    event_type = Column(Text, nullable=False)
    resource_type = Column(Text, nullable=False)
    payload = Column(JsonType, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    trust_alpha = Column(Numeric(10, 4), nullable=False, default=1.0)
    trust_beta = Column(Numeric(10, 4), nullable=False, default=1.0)
    trust_score = Column(Numeric(5, 4), nullable=False, default=0.5)
    trust_updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    transactions = relationship("Transaction", back_populates="agent")
    rolling_stats = relationship("AgentRollingStats", back_populates="agent", uselist=False)
    policy = relationship("Policy", back_populates="agent", uselist=False)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Text, primary_key=True)
    paypal_order_id = Column(Text, unique=True, nullable=False)
    paypal_auth_id = Column(Text, nullable=True)
    paypal_capture_id = Column(Text, nullable=True)
    agent_id = Column(Text, ForeignKey("agents.id"), nullable=False)
    merchant_id = Column(Text, nullable=False)
    merchant_name = Column(Text, nullable=False)
    merchant_category = Column(Text, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(Text, nullable=False, default="USD")
    description = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="PENDING")
    risk_score = Column(Numeric(5, 4), nullable=True)
    risk_threshold = Column(Numeric(5, 4), nullable=True)
    shap_explanation = Column(JsonType, nullable=True)
    policy_violations = Column(JsonType, nullable=True)
    decision = Column(Text, nullable=True)
    decision_reason = Column(Text, nullable=True)
    resolved_by = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    authorized_at = Column(DateTime(timezone=True), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    agent = relationship("Agent", back_populates="transactions")

class AgentRollingStats(Base):
    __tablename__ = "agent_rolling_stats"

    agent_id = Column(Text, ForeignKey("agents.id"), primary_key=True)
    txn_count = Column(Integer, nullable=False, default=0)
    rolling_mean_amount = Column(Numeric(12, 4), nullable=False, default=0.0)
    rolling_std_amount = Column(Numeric(12, 4), nullable=False, default=1.0)
    txn_last_1h = Column(Integer, nullable=False, default=0)
    txn_last_24h = Column(Integer, nullable=False, default=0)
    avg_hour_of_day = Column(Numeric(5, 2), nullable=False, default=12.0)
    std_hour_of_day = Column(Numeric(5, 2), nullable=False, default=6.0)
    known_merchants = Column(JsonType, nullable=False, default=list)
    known_categories = Column(JsonType, nullable=False, default=list)
    daily_spend_today = Column(Numeric(12, 2), nullable=False, default=0.0)
    last_updated = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    agent = relationship("Agent", back_populates="rolling_stats")

class MerchantHistory(Base):
    __tablename__ = "merchant_history"

    merchant_id = Column(Text, primary_key=True)
    merchant_name = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    txn_count = Column(Integer, nullable=False, default=0)
    avg_amount = Column(Numeric(12, 4), nullable=False, default=0.0)
    std_amount = Column(Numeric(12, 4), nullable=False, default=1.0)
    last_seen = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

class Policy(Base):
    __tablename__ = "policies"

    agent_id = Column(Text, ForeignKey("agents.id"), primary_key=True)
    daily_spend_cap = Column(Numeric(12, 2), nullable=True)
    per_txn_cap = Column(Numeric(12, 2), nullable=True)
    merchant_allowlist = Column(JsonType, nullable=False, default=list)
    merchant_denylist = Column(JsonType, nullable=False, default=list)
    category_allowlist = Column(JsonType, nullable=False, default=list)
    category_denylist = Column(JsonType, nullable=False, default=list)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    agent = relationship("Agent", back_populates="policy")

