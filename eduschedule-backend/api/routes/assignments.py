# api/routes/assignments.py
from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel
from typing import Dict
from uuid import UUID

from core.dependencies import get_current_user, supabase

router = APIRouter(
    prefix="/api/assignments",
    tags=["Assignments"],
    dependencies=[Depends(get_current_user)]
)

class MoveRequest(BaseModel):
    assignment_id: int
    new_day: int
    new_period: int

@router.post("/validate-move")
def validate_assignment_move(move: MoveRequest):
    """
    Validates if a dragged-and-dropped assignment is in a valid new slot.
    """
    # 1. Get the details of the assignment being moved
    assignment_to_move = supabase.table('assignments').select("*, candidate:candidates(timetable_id)") \
        .eq('id', move.assignment_id).single().execute().data
    if not assignment_to_move:
        return {"valid": False, "reason": "Assignment not found."}

    candidate_id = assignment_to_move['candidate_id']
    
    # 2. Check for a teacher conflict
    teacher_conflict = supabase.table('assignments').select("id") \
        .eq('candidate_id', candidate_id) \
        .eq('teacher_id', assignment_to_move['teacher_id']) \
        .eq('day_of_week', move.new_day) \
        .eq('period', move.new_period) \
        .execute().data
    if teacher_conflict:
        return {"valid": False, "reason": "Teacher has another class at this time."}

    # 3. Check for a room conflict
    room_conflict = supabase.table('assignments').select("id") \
        .eq('candidate_id', candidate_id) \
        .eq('room_id', assignment_to_move['room_id']) \
        .eq('day_of_week', move.new_day) \
        .eq('period', move.new_period) \
        .execute().data
    if room_conflict:
        return {"valid": False, "reason": "Room is already occupied at this time."}
        
    # 4. Check for a class conflict (the class itself is already scheduled)
    class_conflict = supabase.table('assignments').select("id") \
        .eq('candidate_id', candidate_id) \
        .eq('class_id', assignment_to_move['class_id']) \
        .eq('day_of_week', move.new_day) \
        .eq('period', move.new_period) \
        .execute().data
    if class_conflict:
        return {"valid": False, "reason": "This class already has a lesson at this time."}

    # If no conflicts are found, the move is valid
    return {"valid": True}