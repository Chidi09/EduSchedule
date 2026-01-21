from fastapi import APIRouter, Depends, Body, HTTPException
from pydantic import BaseModel
from core.dependencies import get_current_user, supabase
from supabase import create_client, Client

router = APIRouter(prefix="/api/schools", tags=["Schools"])

class SchoolCreate(BaseModel):
    name: str

@router.post("/")
def create_school(
    school_data: SchoolCreate = Body(...),
    current_user: Client = Depends(get_current_user) # Type hint for clarity
):
    """
    Creates a new school and sets the creator as the owner.
    Also links the user's profile to the new school.
    """
    # Access the 'id' property directly from the Supabase user object
    user_id = current_user.id 
    
    # 1. Create the school
    school_insert_response = supabase.table('schools').insert({
        "name": school_data.name,
        "owner_id": user_id
    }).execute()
    
    if not school_insert_response.data:
        raise HTTPException(status_code=500, detail="Could not create school.")
        
    new_school = school_insert_response.data[0]
    
    # 2. Update the user's record in the 'profiles' table to link them to the new school
    supabase.table('profiles').update({
        "school_id": new_school['id']
    }).eq('id', user_id).execute()
    
    return new_school
