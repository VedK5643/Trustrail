export interface ShapFeature {
  name: string;
  value: number;
  shap_value: number;
  english: string;
}

export interface ShapExplanation {
  features: ShapFeature[];
  counterfactual?: string;
}

export interface PolicyViolation {
  rule: string;
  detail: string;
}

export interface Transaction {
  id: string;
  paypal_order_id: string;
  paypal_auth_id?: string;
  paypal_capture_id?: string;
  agent_id: string;
  merchant_id: string;
  merchant_name: string;
  merchant_category: string;
  amount: number;
  currency: string;
  description?: string;
  status: 'PENDING' | 'AUTHORIZED' | 'AUTO_CAPTURED' | 'HELD' | 'APPROVED' | 'DENIED' | 'CAPTURED' | 'VOIDED';
  risk_score?: number;
  risk_threshold?: number;
  shap_explanation?: ShapExplanation;
  policy_violations?: PolicyViolation[];
  decision?: string;
  decision_reason?: string;
  resolved_by?: string;
  created_at: string;
  resolved_at?: string;
}

export interface Agent {
  id: string;
  name: string;
  description?: string;
  trust_score: number;
  trust_alpha: number;
  trust_beta: number;
  txn_count: number;
  rolling_mean_amount: number;
  daily_spend_today: number;
  known_merchants_count: number;
}

export interface AgentPolicy {
  agent_id: string;
  daily_spend_cap?: number | null;
  per_txn_cap?: number | null;
  merchant_allowlist: string[];
  merchant_denylist: string[];
  category_allowlist: string[];
  category_denylist: string[];
  updated_at?: string;
}

