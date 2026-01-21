from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List
from uuid import UUID
from pydantic import BaseModel, EmailStr
import os

from core.dependencies import get_current_user, supabase
from schemas.data_models import TeacherBase, TeacherCreate

router = APIRouter(
    prefix="/api/teachers",
    tags=["Teachers"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=TeacherBase, status_code=status.HTTP_201_CREATED)
def create_teacher(teacher: TeacherCreate):
    """
    Create a new teacher profile manually.
    """
    response = supabase.table('teachers').insert(teacher.dict()).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create teacher.")
    return response.data[0]

@router.get("/", response_model=List[TeacherBase])
def list_teachers():
    response = supabase.table('teachers').select("*").execute()
    return response.data

class TeacherCreateByAdmin(BaseModel):
    name: str
    email: EmailStr

@router.post("/add")
def add_teacher_by_admin(
    teacher_data: TeacherCreateByAdmin,
    current_user: dict = Depends(get_current_user)
):
    """
    Allows an admin to create a new teacher account using Supabase Admin.
    """
    admin_id = current_user.id

    # 1. Get the admin's school_id
    admin_profile = supabase.table('profiles').select("school_id").eq('id', admin_id).single().execute().data
    if not admin_profile or not admin_profile.get('school_id'):
        raise HTTPException(status_code=403, detail="Admin is not associated with a school.")

    school_id = admin_profile['school_id']

    # 2. Create the user in Supabase Auth (Requires Service Role Key)
    # Note: In a real app, instantiate a separate admin client with the service role key
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase_url = os.environ.get("SUPABASE_URL")

    if not service_role_key:
        raise HTTPException(status_code=500, detail="Server misconfiguration: Missing Service Role Key.")

    from supabase import create_client
    admin_client = create_client(supabase_url, service_role_key)

    try:
        # Create user with a dummy password that they must reset, or use magic link flow
        # Supabase 'invite_user_by_email' is preferred if SMTP is set up
        auth_response = admin_client.auth.admin.invite_user_by_email(teacher_data.email)
        new_user = auth_response.user

        if not new_user:
             raise HTTPException(status_code=400, detail="Failed to create auth user.")

        # 3. Create profile record
        supabase.table('profiles').insert({
            'id': new_user.id,
            'name': teacher_data.name,
            'email': teacher_data.email,
            'role': 'teacher',
            'school_id': school_id
        }).execute()

        # 4. Create teacher record
        supabase.table('teachers').insert({
            'user_id': new_user.id,
            'school_id': school_id
        }).execute()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": f"Teacher '{teacher_data.name}' created. Invitation email sent."}
