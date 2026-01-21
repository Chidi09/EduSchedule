# api/routes/payments.py
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from pydantic import BaseModel
from paystackapi.paystack import Paystack
from core.dependencies import get_current_user, supabase

# Initialize Paystack
paystack = Paystack(secret_key=os.environ.get("PAYSTACK_SECRET_KEY"))

router = APIRouter(prefix="/api/payments", tags=["Payments"])

# Define a Pydantic model for the request body
class SubscriptionRequest(BaseModel):
    planId: str
    amount: int # Amount in kobo

@router.post("/subscribe")
def create_payment_link(
    sub_request: SubscriptionRequest = Body(...), 
    current_user: dict = Depends(get_current_user)
):
    """
    Initializes a Paystack transaction and provides a callback URL.
    """
    email = current_user['email']
    user_id = current_user['uid']
    
    # Use the amount from the request body
    amount = sub_request.amount

    response = paystack.transaction.initialize(
        reference=f"edu_{user_id}_{uuid.uuid4()}", # Unique reference
        amount=amount,
        email=email,
        # Tell Paystack where to redirect the user after payment
        callback_url="http://localhost:5173/payment-success", 
        # Pass our user ID and the plan ID in the metadata
        metadata={"user_id": user_id, "plan_id": sub_request.planId} 
    )
    
    if response.get('status'):
        return {"authorization_url": response['data']['authorization_url']}
    else:
        raise HTTPException(status_code=400, detail="Could not initialize payment.")

@router.post("/webhook")
async def paystack_webhook(request: Request):
    """
    Listens for successful payment events from Paystack.
    This endpoint must be publicly accessible (no auth dependency).
    """
    body = await request.json()
    event = body.get('event')

    if event == 'charge.success':
        user_id = body['data']['metadata']['user_id']
        # Update user's plan in the database to 'premium'
        # Set subscription_expires_at to 1 month or 1 year from now
        # ... supabase.table('users').update({...}).eq('id', user_id).execute() ...
        print(f"Payment successful for user {user_id}. Granting premium access.")
    
    return {"status": "ok"}