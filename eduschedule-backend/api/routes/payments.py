import os
import uuid
import hashlib
import hmac
from fastapi import APIRouter, Depends, HTTPException, Request, Body, Header
from pydantic import BaseModel
from paystackapi.paystack import Paystack
from core.dependencies import get_current_user, supabase

# Initialize Paystack
PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET_KEY")
paystack = Paystack(secret_key=PAYSTACK_SECRET)
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

router = APIRouter(prefix="/api/payments", tags=["Payments"])

class SubscriptionRequest(BaseModel):
    planId: str
    amount: int

@router.post("/subscribe")
def create_payment_link(
    sub_request: SubscriptionRequest = Body(...),
    current_user: dict = Depends(get_current_user)
):
    email = current_user.email
    user_id = current_user.id

    response = paystack.transaction.initialize(
        reference=f"edu_{user_id}_{uuid.uuid4()}",
        amount=sub_request.amount,
        email=email,
        callback_url=f"{FRONTEND_URL}/payment-success",
        metadata={"user_id": user_id, "plan_id": sub_request.planId}
    )

    if response.get('status'):
        return {"authorization_url": response['data']['authorization_url']}
    else:
        raise HTTPException(status_code=400, detail="Could not initialize payment.")

@router.post("/webhook")
async def paystack_webhook(request: Request, x_paystack_signature: str = Header(None)):
    """
    Secure Webhook endpoint.
    """
    body_bytes = await request.body()

    # 1. Verify Signature
    if not PAYSTACK_SECRET:
        print("Error: PAYSTACK_SECRET_KEY not set")
        return {"status": "error"}

    hash_obj = hmac.new(PAYSTACK_SECRET.encode('utf-8'), body_bytes, hashlib.sha512)
    expected_signature = hash_obj.hexdigest()

    if x_paystack_signature != expected_signature:
        raise HTTPException(status_code=403, detail="Invalid signature")

    # 2. Process Event
    body = await request.json()
    event = body.get('event')

    if event == 'charge.success':
        metadata = body['data'].get('metadata', {})
        user_id = metadata.get('user_id')

        if user_id:
            # Update user's profile to premium
            # In a real app, calculate actual expiry date based on plan
            supabase.table('profiles').update({
                "plan": "premium",
                "subscription_status": "active"
            }).eq('id', user_id).execute()

    return {"status": "ok"}
