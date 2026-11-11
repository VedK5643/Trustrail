#!/usr/bin/env python3
"""
PayPal Sandbox Real Connectivity Check

Loads credentials from .env, calls the PayPal Sandbox OAuth2 token endpoint,
and creates a $1.00 AUTHORIZE order against the real sandbox.
Prints the real PayPal Order ID and status, or prints the real error details.
"""

import os
import sys
import base64
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Load .env from project root
root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / ".env"
load_dotenv(dotenv_path=env_path)

CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "").strip()
BASE_URL = os.getenv("PAYPAL_SANDBOX_BASE_URL", "https://api-m.sandbox.paypal.com").rstrip("/")

print("==================================================")
print("  PayPal Sandbox Real Connectivity Verification   ")
print("==================================================")
print(f"Target Base URL: {BASE_URL}")

if not CLIENT_ID or not CLIENT_SECRET or "placeholder" in CLIENT_ID.lower() or "placeholder" in CLIENT_SECRET.lower():
    print("\n❌ ERROR: Real PayPal credentials not detected in .env!")
    print(f"  PAYPAL_CLIENT_ID:     '{CLIENT_ID}'")
    print(f"  PAYPAL_CLIENT_SECRET: '{CLIENT_SECRET[:4]}...' (length: {len(CLIENT_SECRET)})")
    print("\nPlease set your real sandbox credentials in .env and run this script again:")
    print("  PAYPAL_CLIENT_ID=<your-sandbox-client-id>")
    print("  PAYPAL_CLIENT_SECRET=<your-sandbox-client-secret>")
    sys.exit(1)

print(f"\n[1/2] Authenticating via OAuth2 Client Credentials...")
print(f"  Client ID: {CLIENT_ID[:8]}...{CLIENT_ID[-4:]}")

auth_bytes = f"{CLIENT_ID}:{CLIENT_SECRET}".encode("utf-8")
encoded_auth = base64.b64encode(auth_bytes).decode("utf-8")

token_url = f"{BASE_URL}/v1/oauth2/token"
headers = {
    "Authorization": f"Basic {encoded_auth}",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {"grant_type": "client_credentials"}

try:
    with httpx.Client(timeout=15.0) as client:
        token_resp = client.post(token_url, headers=headers, data=data)

    if token_resp.status_code != 200:
        print(f"\n❌ OAuth2 Token Request FAILED (HTTP {token_resp.status_code}):")
        print(token_resp.text)
        sys.exit(1)

    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in")
    print(f"  ✅ SUCCESS: Access token acquired! (Expires in {expires_in} seconds)")

except Exception as e:
    print(f"\n❌ Network / HTTP Connection Error during OAuth2: {e}")
    sys.exit(1)

print(f"\n[2/2] Creating test order with intent=AUTHORIZE ($1.00 USD)...")
orders_url = f"{BASE_URL}/v2/checkout/orders"
order_headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
order_payload = {
    "intent": "AUTHORIZE",
    "purchase_units": [{
        "reference_id": "test_connectivity_001",
        "description": "TrustRail Connectivity Verification Order",
        "amount": {
            "currency_code": "USD",
            "value": "1.00"
        }
    }],
    "payment_source": {
        "paypal": {
            "experience_context": {
                "return_url": "https://trustrail-gamma.vercel.app/",
                "cancel_url": "https://trustrail-gamma.vercel.app/",
                "user_action": "PAY_NOW"
            }
        }
    }
}

try:
    with httpx.Client(timeout=15.0) as client:
        order_resp = client.post(orders_url, headers=order_headers, json=order_payload)

    if order_resp.status_code not in (200, 201):
        print(f"\n❌ Order Creation FAILED (HTTP {order_resp.status_code}):")
        print(order_resp.text)
        sys.exit(1)

    order_info = order_resp.json()
    order_id = order_info.get("id")
    order_status = order_info.get("status")
    links = order_info.get("links", [])
    approve_link = next((l["href"] for l in links if l.get("rel") == "approve"), None)

    print(f"  ✅ SUCCESS: Real PayPal Sandbox Order created!")
    print(f"  Order ID:     {order_id}")
    print(f"  Status:       {order_status}")
    if approve_link:
        print(f"  Approve Link: {approve_link}")

    print("\n==================================================")
    print("  Real PayPal Sandbox connectivity verified 100%! ")
    print("==================================================")

except Exception as e:
    print(f"\n❌ Network / HTTP Connection Error during Order creation: {e}")
    sys.exit(1)

