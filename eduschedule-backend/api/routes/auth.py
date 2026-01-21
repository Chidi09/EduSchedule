# eduschedule-backend/api/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Dict
import random
from datetime import datetime, timedelta

from core.dependencies import get_current_user, supabase

# Create the router instance
router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

# Pydantic model for the request body
class UserCreate(BaseModel):
    email: EmailStr
    name: str

@router.post("/verify")
def verify_and_create_user(user_data: UserCreate, current_user: Dict = Depends(get_current_user)):
    """
    1. Verifies Firebase token (done by `get_current_user` dependency).
    2. Checks if user exists in our Supabase 'users' table.
    3. If not, creates them and may offer a special deal.
    """
    email = current_user.get("email")
    if email != user_data.email:
        raise HTTPException(status_code=400, detail="Token email does not match payload email")

    # Check if user already exists
    response = supabase.table('users').select("id").eq('email', email).execute()
    
    if not response.data:
        # User does not exist, create them
        user_record = {
            'email': email,
            'name': user_data.name
        }
        
        # --- CHANCE DEAL LOGIC ---
        # Give user a 50% chance to get the deal
        if random.random() < 0.5:
            now = datetime.utcnow()
            user_record['deal_offered_at'] = now.isoformat()
            user_record['deal_expires_at'] = (now + timedelta(hours=24)).isoformat()
        # --- END DEAL LOGIC ---
            
        insert_response = supabase.table('users').insert(user_record).execute()
        if not insert_response.data:
            raise HTTPException(status_code=500, detail="Could not create user in database.")
        return {"message": "User verified and created successfully.", "user": insert_response.data[0]}
    
    return {"message": "User verified successfully.", "user": response.data[0]}