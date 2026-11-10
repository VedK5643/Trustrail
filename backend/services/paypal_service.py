import base64
import time
from typing import Dict, Any, Optional
import httpx
from config import settings

class PayPalService:
    def __init__(self):
        self.base_url = settings.PAYPAL_SANDBOX_BASE_URL.rstrip('/')
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    async def get_access_token(self) -> str:
        """
        Retrieves OAuth2 bearer token from PayPal Sandbox using client credentials.
        Caches token until 60 seconds before expiration.
        """
        if not self.client_id or not self.client_secret or "placeholder" in self.client_id.lower() or "placeholder" in self.client_secret.lower():
            raise ValueError(
                "Missing valid PAYPAL_CLIENT_ID or PAYPAL_CLIENT_SECRET in backend configuration. Real PayPal Sandbox credentials are required."
            )

        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        auth_str = f"{self.client_id}:{self.client_secret}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/v1/oauth2/token",
                headers={
                    "Authorization": f"Basic {encoded_auth}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"grant_type": "client_credentials"}
            )
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            expires_in = float(data.get("expires_in", 32400))
            self._token_expires_at = time.time() + expires_in
            return self._access_token

    async def create_order(
        self,
        amount: float,
        currency: str = "USD",
        description: str = "",
        reference_id: str = ""
    ) -> Dict[str, Any]:
        """
        POST /v2/checkout/orders with intent=AUTHORIZE
        """
        token = await self.get_access_token()
        payload = {
            "intent": "AUTHORIZE",
            "purchase_units": [{
                "reference_id": reference_id or "trustrail_ref",
                "description": description or "TrustRail Governed Agent Transaction",
                "amount": {
                    "currency_code": currency,
                    "value": f"{amount:.2f}"
                }
            }],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "return_url": "https://trustrail.local/return",
                        "cancel_url": "https://trustrail.local/cancel",
                        "user_action": "PAY_NOW"
                    }
                }
            }
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/v2/checkout/orders",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            resp.raise_for_status()
            return resp.json()

    async def authorize_order(self, order_id: str) -> Dict[str, Any]:
        """
        POST /v2/checkout/orders/{order_id}/authorize
        """
        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/authorize",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={}
            )
            resp.raise_for_status()
            return resp.json()

    async def capture_authorization(self, authorization_id: str) -> Dict[str, Any]:
        """
        POST /v2/payments/authorizations/{authorization_id}/capture
        """
        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/v2/payments/authorizations/{authorization_id}/capture",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={}
            )
            resp.raise_for_status()
            return resp.json()

    async def void_authorization(self, authorization_id: str) -> bool:
        """
        POST /v2/payments/authorizations/{authorization_id}/void
        """
        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/v2/payments/authorizations/{authorization_id}/void",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={}
            )
            resp.raise_for_status()
            return resp.status_code in (200, 204)

    async def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """
        GET /v2/checkout/orders/{order_id}
        """
        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.base_url}/v2/checkout/orders/{order_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            resp.raise_for_status()
            return resp.json()

    async def verify_webhook_signature(self, headers: Dict[str, str], raw_body: Dict[str, Any]) -> bool:
        """
        POST /v1/notifications/verify-webhook-signature
        """
        token = await self.get_access_token()
        payload = {
            "auth_algo": headers.get("paypal-auth-algo", ""),
            "cert_url": headers.get("paypal-cert-url", ""),
            "transmission_id": headers.get("paypal-transmission-id", ""),
            "transmission_sig": headers.get("paypal-transmission-sig", ""),
            "transmission_time": headers.get("paypal-transmission-time", ""),
            "webhook_id": settings.PAYPAL_WEBHOOK_ID,
            "webhook_event": raw_body
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/v1/notifications/verify-webhook-signature",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("verification_status") == "SUCCESS"
            return False

    async def list_disputes(self) -> Dict[str, Any]:
        """
        GET /v1/customer/disputes
        """
        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.base_url}/v1/customer/disputes",
                headers={"Authorization": f"Bearer {token}"}
            )
            resp.raise_for_status()
            return resp.json()

    async def get_dispute(self, dispute_id: str) -> Dict[str, Any]:
        """
        GET /v1/customer/disputes/{dispute_id}
        """
        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.base_url}/v1/customer/disputes/{dispute_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            resp.raise_for_status()
            return resp.json()

paypal_service = PayPalService()
