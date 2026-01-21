from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List
from uuid import UUID
from pydantic import BaseModel, EmailStr
import os

from core.dependencies import get_current_user, supabase
from core.rbac import admin_required, teacher_or_admin_required, require_permission, validate_school_access, log_rbac_violation
from schemas.data_models import TeacherBase, TeacherCreate

router = APIRouter(
    prefix="/api/teachers",
    tags=["Teachers"]
)

@router.post("/", response_model=TeacherBase, status_code=status.HTTP_201_CREATED)
def create_teacher(teacher: TeacherCreate, admin_user: dict = Depends(admin_required)):
    """
    Create a new teacher profile manually. Admin only.
    """
    # Ensure teacher is created in admin's school
    teacher_data = teacher.dict()
    teacher_data['school_id'] = admin_user['school_id']

    response = supabase.table('teachers').insert(teacher_data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create teacher.")
    return response.data[0]

@router.get("/", response_model=List[TeacherBase])
def list_teachers(user: dict = Depends(teacher_or_admin_required)):
    """
    List teachers in the same school as the current user.
    """
    # Teachers and admins can only see teachers from their own school
    response = supabase.table('teachers').select("*").eq('school_id', user['school_id']).execute()
    return response.data

class TeacherCreateByAdmin(BaseModel):
    name: str
    email: EmailStr

@router.post("/add")
def add_teacher_by_admin(
    teacher_data: TeacherCreateByAdmin,
    admin_user: dict = Depends(admin_required)
):
    """
    Allows an admin to create a new teacher account using Supabase Admin.
    Strict RBAC enforcement - Admin only, same school only.
    """
    # Verify admin has permission to create teachers
    require_permission(admin_user, "create_teacher")

    school_id = admin_user['school_id']
    if not school_id:
        raise HTTPException(status_code=403, detail="Admin is not associated with a school.")

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
        # Log the security event
        log_rbac_violation(
            admin_user['id'],
            "create_teacher_failed",
            teacher_data.email,
            str(e)
        )
        raise HTTPException(status_code=400, detail=f"Failed to create teacher: {str(e)}")

    return {"message": f"Teacher '{teacher_data.name}' created. Invitation email sent."}

@router.get("/{teacher_id}")
def get_teacher(teacher_id: str, user: dict = Depends(teacher_or_admin_required)):
    """
    Get a specific teacher. Must be in same school.
    """
    teacher = supabase.table('teachers').select("*").eq('id', teacher_id).single().execute().data
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Verify same school access
    validate_school_access(user, teacher['school_id'])

    return teacher

@router.delete("/{teacher_id}")
def delete_teacher(teacher_id: str, admin_user: dict = Depends(admin_required)):
    """
    Delete a teacher. Admin only, same school only.
    """
    require_permission(admin_user, "delete_teacher")

    # Get teacher to verify school
    teacher = supabase.table('teachers').select("*").eq('id', teacher_id).single().execute().data
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Verify same school
    validate_school_access(admin_user, teacher['school_id'])

    # Delete teacher
    result = supabase.table('teachers').delete().eq('id', teacher_id).execute()
    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to delete teacher")

    return {"message": "Teacher deleted successfully"}

@router.patch("/{teacher_id}")
def update_teacher(
    teacher_id: str,
    updates: dict,
    user: dict = Depends(teacher_or_admin_required)
):
    """
    Update teacher information. Admins can update any teacher in their school.
    Teachers can only update their own profile.
    """
    # Get teacher
    teacher = supabase.table('teachers').select("*").eq('id', teacher_id).single().execute().data
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Verify access
    validate_school_access(user, teacher['school_id'])

    # Additional check: teachers can only edit their own profile
    if user['role'] == 'teacher' and teacher['user_id'] != user['id']:
        log_rbac_violation(
            user['id'],
            "unauthorized_teacher_update",
            teacher_id,
            "Teacher tried to update another teacher's profile"
        )
        raise HTTPException(status_code=403, detail="Teachers can only update their own profile")

    # Update teacher
    result = supabase.table('teachers').update(updates).eq('id', teacher_id).execute()
    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to update teacher")

    return result.data[0]
