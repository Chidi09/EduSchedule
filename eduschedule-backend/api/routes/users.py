# api/routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
import secrets
import hashlib
from datetime import datetime, timezone
from core.dependencies import get_current_user, supabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["Users"])

def hash_api_key(api_key: str) -> str:
    """Hash an API key using SHA256"""
    return hashlib.sha256(api_key.encode()).hexdigest()

@router.get("/", dependencies=[Depends(get_current_user)])
def list_users():
    """
    Retrieves a list of all users from profiles table.
    """
    response = supabase.table('profiles').select("id, name, email, role, school_id").execute()
    return response.data

@router.post("/me/apikeys")
def create_api_key_for_user(current_user: dict = Depends(get_current_user)):
    """
    Generates a new API key for the currently authenticated user.
    SECURITY: Only stores the hash of the key in database.
    """
    user_id = current_user.id

    # Generate a new secure, URL-safe key
    new_key = f"edusk_{secrets.token_urlsafe(32)}"
    key_hash = hash_api_key(new_key)

    # Generate a readable name for the key (first 8 chars for identification)
    key_preview = f"...{new_key[-8:]}"

    key_data = {
        "user_id": user_id,
        "key_hash": key_hash,  # Store only the hash
        "key_preview": key_preview,  # For user to identify their keys
        "description": "Default API Key",
        "created_at": datetime.utcnow().isoformat(),
        "last_used": None,
        "is_active": True
    }

    try:
        db_response = supabase.table('api_keys').insert(key_data).execute()

        if not db_response.data:
            logger.error(f"Failed to create API key for user {user_id}")
            raise HTTPException(status_code=500, detail="Could not create API key.")

        logger.info(f"API key created for user {user_id}")

        return {
            "message": "API key created successfully. Store it securely, as it will not be shown again.",
            "api_key": new_key,  # Show the actual key only once
            "key_id": db_response.data[0]['id'],
            "key_preview": key_preview
        }
    except Exception as e:
        logger.error(f"Error creating API key for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create API key")

@router.get("/me/apikeys")
def list_my_api_keys(current_user: dict = Depends(get_current_user)):
    """
    List all API keys for the current user (without showing the actual keys).
    """
    user_id = current_user.id

    response = supabase.table('api_keys').select(
        "id, key_preview, description, created_at, last_used, is_active"
    ).eq('user_id', user_id).execute()

    return response.data

@router.delete("/me/apikeys/{key_id}")
def delete_api_key(key_id: str, current_user: dict = Depends(get_current_user)):
    """
    Delete a specific API key for the current user.
    """
    user_id = current_user.id

    # Verify the key belongs to the current user
    key_response = supabase.table('api_keys').select("user_id").eq('id', key_id).single().execute()

    if not key_response.data:
        raise HTTPException(status_code=404, detail="API key not found")

    if key_response.data['user_id'] != user_id:
        logger.warning(f"User {user_id} attempted to delete API key {key_id} belonging to another user")
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete the key
    delete_response = supabase.table('api_keys').delete().eq('id', key_id).execute()

    if not delete_response.data:
        raise HTTPException(status_code=500, detail="Failed to delete API key")

    logger.info(f"API key {key_id} deleted by user {user_id}")
    return {"message": "API key deleted successfully"}

@router.get("/me/deal-status")
def get_user_deal_status(current_user: dict = Depends(get_current_user)):
    """
    Checks if the current user has an active special deal.
    """
    user_id = current_user.id
    response = supabase.table('profiles').select("deal_expires_at").eq('id', user_id).single().execute()

    if response.data and response.data.get('deal_expires_at'):
        expires_at_str = response.data['deal_expires_at']
        try:
            # Handle timezone-aware datetime parsing
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)

            if expires_at > now:
                expires_in_seconds = (expires_at - now).total_seconds()
                return {"isActive": True, "expiresIn": int(expires_in_seconds)}
        except (ValueError, AttributeError) as e:
            logger.error(f"Error parsing deal expiry date for user {user_id}: {str(e)}")

    return {"isActive": False, "expiresIn": 0}

@router.get("/me")
def get_my_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Fetches the full profile for the currently logged-in user.
    """
    user_id = current_user.id
    logger.info(f"Fetching profile for user: {user_id}")

    response = supabase.table('profiles').select("*").eq('id', user_id).single().execute()

    if not response.data:
        logger.warning(f"Profile not found for user {user_id}")
        raise HTTPException(status_code=404, detail="User profile not found.")

    return response.data

@router.patch("/me")
def update_my_profile(updates: dict, current_user: dict = Depends(get_current_user)):
    """
    Update the current user's profile. Users can only update specific fields.
    """
    user_id = current_user.id

    # Define allowed fields that users can update themselves
    allowed_fields = ['name', 'email']  # Note: role and school_id require admin approval

    # Filter updates to only allowed fields
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

    if not filtered_updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    # Add timestamp
    filtered_updates['updated_at'] = datetime.utcnow().isoformat()

    try:
        response = supabase.table('profiles').update(filtered_updates).eq('id', user_id).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to update profile")

        logger.info(f"Profile updated for user {user_id}")
        return response.data[0]
    except Exception as e:
        logger.error(f"Error updating profile for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

def verify_api_key(api_key: str) -> dict:
    """
    Verify an API key by checking its hash against the database.
    Returns user info if valid, raises HTTPException if invalid.
    This function can be used by other routes for API key authentication.
    """
    if not api_key.startswith("edusk_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")

    key_hash = hash_api_key(api_key)

    # Find the key in database
    key_response = supabase.table('api_keys').select(
        "user_id, is_active, last_used"
    ).eq('key_hash', key_hash).single().execute()

    if not key_response.data:
        logger.warning(f"Invalid API key attempt: {api_key[:20]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")

    key_data = key_response.data

    if not key_data['is_active']:
        raise HTTPException(status_code=401, detail="API key is deactivated")

    # Update last used timestamp
    supabase.table('api_keys').update({
        'last_used': datetime.utcnow().isoformat()
    }).eq('key_hash', key_hash).execute()

    # Get user profile
    user_response = supabase.table('profiles').select("*").eq('id', key_data['user_id']).single().execute()

    if not user_response.data:
        raise HTTPException(status_code=401, detail="User not found for API key")

    return user_response.data
