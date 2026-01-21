import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client, Client
from dotenv import load_dotenv # <-- Uncomment this line

# This function is essential for loading your .env file
load_dotenv() # <-- Uncomment this line

# --- Supabase Initialization ---
url: str = os.environ.get("SUPABASE_URL")
# Use the SERVICE_ROLE_KEY for backend operations
key: str = os.environ.get("SUPABASE_KEY") 
supabase: Client = create_client(url, key)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency to verify a Supabase JWT and get user data.
    """
    try:
        # Use the Supabase client to validate the token
        user_response = supabase.auth.get_user(token)
        return user_response.user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )