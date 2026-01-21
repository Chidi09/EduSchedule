# api/routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from core.dependencies import get_current_user, supabase
import secrets
from datetime import datetime, timezone

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/", dependencies=[Depends(get_current_user)])
def list_users():
    """
    Retrieves a list of all users.
    """
    response = supabase.table('users').select("id, name, email").execute()
    return response.data

@router.post("/me/apikeys")
def create_api_key_for_user(current_user: dict = Depends(get_current_user)):
    """
    Generates a new API key for the currently authenticated user.
    """
    user_id = current_user.get('uid')
    
    # Generate a new secure, URL-safe key
    new_key = f"edusk_{secrets.token_urlsafe(32)}"
    
    key_data = {
        "user_id": user_id,
        "key": new_key,
        "description": "Default API Key"
    }
    
    db_response = supabase.table('api_keys').insert(key_data).execute()
    
    if not db_response.data:
        raise HTTPException(status_code=500, detail="Could not create API key.")
        
    return {
        "message": "API key created successfully. Store it securely, as it will not be shown again.",
        "api_key": new_key
    }

@router.get("/me/deal-status")
def get_user_deal_status(current_user: dict = Depends(get_current_user)):
    """
    Checks if the current user has an active special deal.
    """
    user_id = current_user.get("uid")
    response = supabase.table('users').select("deal_expires_at").eq('id', user_id).single().execute()
    
    if response.data and response.data.get('deal_expires_at'):
        expires_at_str = response.data['deal_expires_at']
        # Ensure correct timezone handling
        expires_at = datetime.fromisoformat(expires_at_str).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        
        if expires_at > now:
            expires_in_seconds = (expires_at - now).total_seconds()
            return {"isActive": True, "expiresIn": int(expires_in_seconds)}
            
    return {"isActive": False, "expiresIn": 0}

@router.get("/me")
def get_my_user_profile(current_user: dict = Depends(get_current_user)):
    """Fetches the full profile for the currently logged-in user."""
    user_id = current_user.get("uid")
    print(f"--- DEBUG: Attempting to fetch profile for Firebase UID: {user_id} ---") # Add this log

    response = supabase.table('users').select("*").eq('id', user_id).single().execute()
    
    print(f"--- DEBUG: Supabase response: {response.data} ---") # Add this log

    if not response.data:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return response.data