from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from core.dependencies import get_current_user, supabase
from core.permissions import check_plan_limits
from schemas.data_models import RoomBase, RoomCreate

router = APIRouter(
    prefix="/api/rooms",
    tags=["Rooms"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=RoomBase, status_code=status.HTTP_201_CREATED)
def create_room(
    room: RoomCreate,
    user: dict = Depends(get_current_user),
    _: dict = Depends(check_plan_limits("rooms"))
):
    """Create a new room. Plan limits enforced."""
    room_data = room.dict()
    room_data['user_id'] = user.id
    response = supabase.table('rooms').insert(room_data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create room.")
    return response.data[0]

@router.get("/", response_model=List[RoomBase])
def list_rooms():
    response = supabase.table('rooms').select("*").execute()
    return response.data
