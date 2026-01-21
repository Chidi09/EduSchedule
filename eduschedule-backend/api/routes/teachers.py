# api/routes/teachers.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Dict
from uuid import UUID
from pydantic import BaseModel, EmailStr
from firebase_admin import auth

from core.dependencies import get_current_user, supabase
from schemas.data_models import TeacherBase, TeacherCreate

router = APIRouter(
    prefix="/api/teachers",
    tags=["Teachers"],
    dependencies=[Depends(get_current_user)] # Protect all routes in this router
)

@router.post("/", response_model=TeacherBase, status_code=status.HTTP_201_CREATED)
def create_teacher(teacher: TeacherCreate):
    """
    Create a new teacher.
    Note: Assumes the user_id exists in the 'users' table.
    """
    response = supabase.table('teachers').insert(teacher.dict()).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create teacher.")
    return response.data[0]

@router.get("/", response_model=List[TeacherBase])
def list_teachers():
    """
    Retrieve a list of all teachers.
    """
    response = supabase.table('teachers').select("*").execute()
    return response.data

@router.get("/{teacher_id}", response_model=TeacherBase)
def get_teacher(teacher_id: UUID):
    """
    Retrieve a single teacher by their ID.
    """
    response = supabase.table('teachers').select("*").eq('id', str(teacher_id)).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Teacher not found.")
    return response.data

@router.get("/me", response_model=TeacherBase)
def get_my_teacher_profile(current_user: dict = Depends(get_current_user)):
    """Fetches the teacher profile for the currently logged-in user."""
    user_id = current_user.get("uid")
    response = supabase.table('teachers').select("*").eq('user_id', user_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Teacher profile not found for this user.")
    return response.data

@router.patch("/me")
def update_my_teacher_preferences(preferences: dict, current_user: dict = Depends(get_current_user)):
    """Updates the preferences for the currently logged-in teacher."""
    user_id = current_user.get("uid")
    response = supabase.table('teachers').update({"preferences": preferences}).eq('user_id', user_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Could not update preferences for this teacher.")
    return {"message": "Preferences updated successfully."}

class TeacherCreateByAdmin(BaseModel):
    name: str
    email: EmailStr

@router.post("/add")
def add_teacher_by_admin(
    teacher_data: TeacherCreateByAdmin,
    current_user: dict = Depends(get_current_user)
):
    """
    Allows an admin to create a new teacher account.
    This creates a Firebase user and sends a password reset email.
    """
    admin_id = current_user.get("uid")
    
    # 1. Get the admin's school_id from the users table
    admin_profile = supabase.table('users').select("school_id").eq('id', admin_id).single().execute().data
    if not admin_profile or not admin_profile.get('school_id'):
        raise HTTPException(status_code=403, detail="Admin is not associated with a school.")
    
    school_id = admin_profile['school_id']

    try:
        # 2. Create the new user in Firebase Authentication
        new_user = auth.create_user(
            email=teacher_data.email,
            display_name=teacher_data.name,
            email_verified=False
        )
        
        # 3. Create a user record in our Supabase 'users' table
        supabase.table('users').insert({
            'id': new_user.uid,
            'name': teacher_data.name,
            'email': teacher_data.email,
            'role': 'teacher',
            'school_id': school_id
        }).execute()

        # 4. Create the corresponding teacher record in our 'teachers' table
        supabase.table('teachers').insert({
            'user_id': new_user.uid,
            'school_id': school_id
        }).execute()

        # 5. Send the teacher an email to set their password
        password_reset_link = auth.generate_password_reset_link(new_user.email)
        # In a real app, you would use a service like SendGrid to email this link.
        # For now, we'll print it to the console for testing.
        print(f"Password setup link for {new_user.email}: {password_reset_link}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": f"Teacher '{teacher_data.name}' created successfully. A setup email has been sent."}