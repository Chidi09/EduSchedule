from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from core.dependencies import get_current_user, supabase
from core.permissions import check_plan_limits
from schemas.data_models import SubjectBase, SubjectCreate

router = APIRouter(
    prefix="/api/subjects",
    tags=["Subjects"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=SubjectBase, status_code=status.HTTP_201_CREATED)
def create_subject(
    subject: SubjectCreate,
    user: dict = Depends(get_current_user),
    _: dict = Depends(check_plan_limits("subjects"))
):
    """Create a new subject. Plan limits enforced."""
    subject_data = subject.dict()
    subject_data['user_id'] = user.id
    response = supabase.table('subjects').insert(subject_data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create subject.")
    return response.data[0]

@router.get("/", response_model=List[SubjectBase])
def list_subjects():
    response = supabase.table('subjects').select("*").execute()
    return response.data
