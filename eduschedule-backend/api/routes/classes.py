from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from core.dependencies import get_current_user, supabase
from core.permissions import check_plan_limits
from schemas.data_models import ClassBase, ClassCreate

router = APIRouter(
    prefix="/api/classes",
    tags=["Classes"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=ClassBase, status_code=status.HTTP_201_CREATED)
def create_class(
    class_item: ClassCreate,
    user: dict = Depends(get_current_user),
    _: dict = Depends(check_plan_limits("classes"))
):
    """Create a new class. Plan limits enforced."""
    class_data = class_item.dict()
    class_data['user_id'] = user.id
    response = supabase.table('classes').insert(class_data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create class.")
    return response.data[0]

@router.get("/", response_model=List[ClassBase])
def list_classes():
    response = supabase.table('classes').select("*").execute()
    return response.data
