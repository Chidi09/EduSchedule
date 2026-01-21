from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Dict
import random
from datetime import datetime, timedelta

from core.dependencies import get_current_user, supabase

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

class UserCreate(BaseModel):
    email: EmailStr
    name: str

@router.post("/verify")
def verify_and_create_user(user_data: UserCreate, current_user: dict = Depends(get_current_user)):
    """
    Verifies Supabase token and ensures a profile exists in the 'profiles' table.
    """
    # current_user is the user object from Supabase Auth
    user_id = current_user.id
    email = current_user.email

    if email != user_data.email:
        raise HTTPException(status_code=400, detail="Token email does not match payload email")

    # Check if profile already exists
    response = supabase.table('profiles').select("*").eq('id', user_id).execute()

    if not response.data:
        # Profile does not exist, create it
        user_record = {
            'id': user_id,  # Link to auth.users
            'email': email,
            'name': user_data.name,
            'role': 'admin'  # Default role for self-registered users
        }

        # --- CHANCE DEAL LOGIC ---
        if random.random() < 0.5:
            now = datetime.utcnow()
            user_record['deal_offered_at'] = now.isoformat()
            user_record['deal_expires_at'] = (now + timedelta(hours=24)).isoformat()
        # --- END DEAL LOGIC ---

        insert_response = supabase.table('profiles').insert(user_record).execute()
        if not insert_response.data:
            raise HTTPException(status_code=500, detail="Could not create user profile.")
        return {"message": "User verified and created successfully.", "user": insert_response.data[0]}

    return {"message": "User verified successfully.", "user": response.data[0]}
