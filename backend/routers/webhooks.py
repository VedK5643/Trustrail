"""
STRETCH / OPTIONAL ENDPOINT (Not wired into the core local Scenario A/B/C demo flow).
Requires a publicly reachable HTTPS callback URL and a configured PAYPAL_WEBHOOK_ID
for PayPal signature verification via /v1/notifications/verify-webhook-signature.
"""
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.engine import get_db
from db.models import RawWebhookEvent
from services.paypal_service import paypal_service

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/paypal")
async def paypal_webhook_handler(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    headers = dict(request.headers)
    body = await request.json()

    # Signature verification
    is_valid = await paypal_service.verify_webhook_signature(headers, body)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid PayPal webhook signature")

    event_id = body.get("id")
    event_type = body.get("event_type", "UNKNOWN")
    resource_type = body.get("resource_type", "UNKNOWN")

    if event_id:
        raw_event = RawWebhookEvent(
            paypal_event_id=event_id,
            event_type=event_type,
            resource_type=resource_type,
            payload=body
        )
        db.add(raw_event)
        try:
            await db.commit()
        except Exception:
            await db.rollback() # Event might already be logged

    return {"status": "SUCCESS", "event_id": event_id, "event_type": event_type}

