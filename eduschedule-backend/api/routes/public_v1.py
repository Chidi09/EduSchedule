from fastapi import APIRouter, Depends, Body
from typing import Dict, Any

# Import the correct, existing dependency
from core.dependencies import get_current_user

router = APIRouter(
    prefix="/v1", 
    tags=["Public API v1"],
    # Use the standard user dependency to protect all routes
    dependencies=[Depends(get_current_user)] 
)

@router.get("/status")
def get_api_status():
    """A simple endpoint to check if the API is up and the user token is valid."""
    return {"status": "ok", "message": "User token is valid."}

@router.post("/timetables/generate")
def generate_timetable_via_api(
    constraints: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    An example endpoint for external services to generate a timetable.
    """
    # The user is now authenticated via their standard Supabase JWT
    user_id = current_user.id
    
    print(f"API request received from user {user_id} with constraints: {constraints}")
    
    return {
        "message": f"Timetable generation job started for API user {user_id}.",
        "job_id": "some_unique_job_id"
    }