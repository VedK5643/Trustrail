export interface PayPalOrderResponse {
  id: string;
  status: string;
  links?: Array<{ rel: string; href: string; method?: string }>;
}

export interface PayPalAuthResponse {
  id: string;
  status: string;
  purchase_units: Array<{
    payments: {
      authorizations: Array<{
        id: string;
        status: string;
        amount: { currency_code: string; value: string };
      }>;
    };
  }>;
}

export interface EvaluationPayload {
  paypal_order_id: string;
  paypal_auth_id: string;
  agent_id: string;
  merchant_id: string;
  merchant_name: string;
  merchant_category: string;
  amount: number;
  currency?: string;
  description?: string;
}

export interface EvaluationResponse {
  id: string;
  paypal_order_id: string;
  paypal_auth_id: string;
  paypal_capture_id?: string;
  status: 'AUTO_CAPTURED' | 'HELD' | 'VOIDED' | 'CAPTURED' | 'DENIED';
  decision: 'AUTO_CLEAR' | 'HOLD' | 'POLICY_BLOCK' | 'APPROVED' | 'DENIED';
  decision_reason?: string;
  risk_score?: number;
  risk_threshold?: number;
  shap_explanation?: {
    features: Array<{
      name: string;
      value: number;
      shap_value: number;
      english: string;
    }>;
    counterfactual?: string;
  };
  policy_violations?: Array<{
    rule: string;
    detail: string;
  }>;
}

export interface AgentPurchaseRequest {
  item: string;
  merchantId: string;
  merchantName: string;
  merchantCategory: string;
  amount: number;
  justification: string;
}

