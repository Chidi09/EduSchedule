from fastapi import APIRouter
from core.dependencies import supabase

router = APIRouter(prefix="/api/public", tags=["Public"])

@router.get("/timetables/{school_id}")
def get_public_timetables(school_id: str):
    """
    Fetches all active timetables (academic, test, exam) for a given school.
    This endpoint is public and does not require authentication.
    """
    # In a real multi-school system, you'd use school_id to filter.
    # For now, we'll fetch all active timetables.
    
    response = supabase.table('timetables') \
        .select("id, term, type, generated_at, assignments(*)") \
        .eq('active', True) \
        .execute().data
        
    return response