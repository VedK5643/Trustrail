import axios from 'axios';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import { PayPalOrderResponse, PayPalAuthResponse, EvaluationPayload, EvaluationResponse } from './types.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, '../../../.env') });

export class PayPalAgentClient {
  private clientId: string;
  private clientSecret: string;
  private baseUrl: string;
  private backendUrl: string;
  private token: string | null = null;
  private tokenExpiresAt: number = 0;

  constructor() {
    this.clientId = process.env.PAYPAL_CLIENT_ID || '';
    this.clientSecret = process.env.PAYPAL_CLIENT_SECRET || '';
    this.baseUrl = (process.env.PAYPAL_SANDBOX_BASE_URL || 'https://api-m.sandbox.paypal.com').replace(/\/$/, '');
    this.backendUrl = (process.env.BACKEND_URL || 'http://localhost:8000').replace(/\/$/, '');
  }

  async getAccessToken(): Promise<string> {
    if (!this.clientId || !this.clientSecret || this.clientId.includes('placeholder') || this.clientSecret.includes('placeholder')) {
      throw new Error(
        '[PayPal] Missing valid PAYPAL_CLIENT_ID or PAYPAL_CLIENT_SECRET in environment. Real PayPal Sandbox credentials are required.'
      );
    }

    // Reuse token until 60 seconds before expiration
    if (this.token && Date.now() < this.tokenExpiresAt - 60000) {
      return this.token;
    }

    const auth = Buffer.from(`${this.clientId}:${this.clientSecret}`).toString('base64');
    const resp = await axios.post(
      `${this.baseUrl}/v1/oauth2/token`,
      'grant_type=client_credentials',
      {
        headers: {
          Authorization: `Basic ${auth}`,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    this.token = resp.data.access_token;
    const expiresInSec = typeof resp.data.expires_in === 'number' ? resp.data.expires_in : 32400;
    this.tokenExpiresAt = Date.now() + expiresInSec * 1000;
    return this.token!;
  }

  /**
   * Creates an order with intent=AUTHORIZE so capture is gated on TrustRail's decision.
   */
  async createAuthorizeOrder(
    amount: number,
    description: string,
    merchantEmail?: string
  ): Promise<PayPalOrderResponse> {
    const token = await this.getAccessToken();
    const payload = {
      intent: 'AUTHORIZE',
      purchase_units: [
        {
          description: description.substring(0, 120),
          amount: {
            currency_code: 'USD',
            value: amount.toFixed(2),
          },
          ...(merchantEmail ? { payee: { email_address: merchantEmail } } : {}),
        },
      ],
      payment_source: {
        paypal: {
          experience_context: {
            return_url: 'https://trustrail-gamma.vercel.app/',
            cancel_url: 'https://trustrail-gamma.vercel.app/',
            user_action: 'PAY_NOW',
          },
        },
      },
    };

    const resp = await axios.post(`${this.baseUrl}/v2/checkout/orders`, payload, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    return resp.data;
  }

  /**
   * Authorizes the order funds.
   */
  async authorizeOrder(orderId: string): Promise<string> {
    const token = await this.getAccessToken();
    const resp = await axios.post<PayPalAuthResponse>(
      `${this.baseUrl}/v2/checkout/orders/${orderId}/authorize`,
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );

    const authId = resp.data.purchase_units?.[0]?.payments?.authorizations?.[0]?.id;
    if (!authId) {
      throw new Error(`Failed to retrieve authorization ID for order ${orderId}. PayPal response: ${JSON.stringify(resp.data)}`);
    }
    return authId;
  }

  /**
   * Submits the authorized transaction to TrustRail spend firewall.
   */
  async submitForGovernance(payload: EvaluationPayload): Promise<EvaluationResponse> {
    const resp = await axios.post<EvaluationResponse>(
      `${this.backendUrl}/api/evaluate`,
      payload,
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 15000,
      }
    );
    return resp.data;
  }
}

export const paypalAgentClient = new PayPalAgentClient();
