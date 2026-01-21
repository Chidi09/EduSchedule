from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from core.dependencies import get_current_user, supabase
from schemas.data_models import ClassBase, ClassCreate

router = APIRouter(
    prefix="/api/classes",
    tags=["Classes"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=ClassBase, status_code=status.HTTP_201_CREATED)
def create_class(class_item: ClassCreate):
    response = supabase.table('classes').insert(class_item.dict()).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create class.")
    return response.data[0]

@router.get("/", response_model=List[ClassBase])
def list_classes():
    response = supabase.table('classes').select("*").execute()
    return response.data