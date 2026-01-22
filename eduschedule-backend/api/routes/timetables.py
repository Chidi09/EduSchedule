import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from core.dependencies import get_current_user, supabase
from services.scheduler import TimetableScheduler
from services.ai_orchestrator import extract_metrics, rank_candidates_with_gemini, explain_candidate_with_gpt
import uuid
import concurrent.futures

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/timetables", tags=["Timetables"], dependencies=[Depends(get_current_user)])

# Initialize rate limiter for this router
limiter = Limiter(key_func=get_remote_address)

# Create a thread pool for heavy calculations
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

def run_solver(teachers_data, rooms_data, subjects_data, classes_data, teacher_subjects_data):
    """Helper function to run solver synchronously"""
    logger.info(f"Running solver with {len(teachers_data)} teachers, {len(classes_data)} classes")
    scheduler = TimetableScheduler(teachers_data, rooms_data, subjects_data, classes_data, teacher_subjects_data)
    solutions = scheduler.solve(solution_limit=5)
    logger.info(f"Solver completed, found {len(solutions)} solutions")
    return solutions

@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/hour")
async def generate_timetable(request: Request):
    # 1. Fetch data (IO bound, okay to await)
    teachers = supabase.table('teachers').select("*").execute().data
    rooms = supabase.table('rooms').select("*").execute().data
    subjects = supabase.table('subjects').select("*").execute().data
    classes = supabase.table('classes').select("*").execute().data
    # You might need a join table for teacher_subjects in your schema
    teacher_subjects = []  # Placeholder: fetch this from your relation table

    if not teachers or not classes:
        raise HTTPException(status_code=400, detail="Insufficient data to generate timetable.")

    # 2. Run solver in background thread (CPU bound) - NO DATABASE CHANGES YET
    loop = asyncio.get_event_loop()
    try:
        solutions = await loop.run_in_executor(
            executor,
            run_solver,
            teachers, rooms, subjects, classes, teacher_subjects
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solver error: {str(e)}")

    if not solutions:
        raise HTTPException(status_code=500, detail="Could not find any valid solutions.")

    # 3. ONLY NOW create database records (transactional integrity)
    try:
        # Create timetable only after successful generation
        new_timetable = supabase.table('timetables').insert({"term": "Fall 2025"}).execute().data[0]

        for solution in solutions:
            candidate_id = str(uuid.uuid4())
            metrics = extract_metrics(solution, teachers)

            # Create candidate record
            candidate_result = supabase.table('candidates').insert({
                "id": candidate_id,
                "timetable_id": new_timetable['id'],
                "metrics": metrics
            }).execute()

            if not candidate_result.data:
                raise Exception(f"Failed to create candidate {candidate_id}")

            # Create assignment records
            assignments_with_ids = []
            for assignment in solution:
                assignment_copy = assignment.copy()
                assignment_copy['candidate_id'] = candidate_id
                assignment_copy['timetable_id'] = new_timetable['id']
                assignments_with_ids.append(assignment_copy)

            assignment_result = supabase.table('assignments').insert(assignments_with_ids).execute()
            if not assignment_result.data:
                raise Exception(f"Failed to create assignments for candidate {candidate_id}")

        return {"message": f"{len(solutions)} candidates generated.", "timetable_id": new_timetable['id']}

    except Exception as e:
        # If database operations fail, clean up any partial data
        if 'new_timetable' in locals():
            try:
                # Delete the timetable and cascade will handle candidates/assignments
                supabase.table('timetables').delete().eq('id', new_timetable['id']).execute()
            except:
                pass  # Best effort cleanup

        raise HTTPException(status_code=500, detail=f"Database error during timetable creation: {str(e)}")

@router.get("/")
async def get_timetables():
    """Get all timetables"""
    response = supabase.table('timetables').select("*").execute()
    return response.data

@router.get("/{timetable_id}")
async def get_timetable(timetable_id: str):
    """Get specific timetable with its candidates"""
    timetable = supabase.table('timetables').select("*").eq('id', timetable_id).single().execute()
    if not timetable.data:
        raise HTTPException(status_code=404, detail="Timetable not found")

    candidates = supabase.table('candidates').select("*").eq('timetable_id', timetable_id).execute()

    return {
        "timetable": timetable.data,
        "candidates": candidates.data
    }

@router.post("/{timetable_id}/rank")
async def rank_candidates(timetable_id: str):
    """Rank candidates using AI"""
    candidates = supabase.table('candidates').select("*").eq('timetable_id', timetable_id).execute().data

    if not candidates:
        raise HTTPException(status_code=404, detail="No candidates found for this timetable")

    try:
        rankings = await asyncio.get_event_loop().run_in_executor(
            executor,
            rank_candidates_with_gemini,
            candidates
        )

        # Update candidates with rankings
        for candidate, rank in zip(candidates, rankings):
            supabase.table('candidates').update({"rank": rank}).eq('id', candidate['id']).execute()

        return {"message": "Candidates ranked successfully", "rankings": rankings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ranking error: {str(e)}")

@router.get("/{timetable_id}/candidates/{candidate_id}/explain")
async def explain_candidate(timetable_id: str, candidate_id: str):
    """Get AI explanation for a specific candidate"""
    candidate = supabase.table('candidates').select("*").eq('id', candidate_id).single().execute()
    if not candidate.data:
        raise HTTPException(status_code=404, detail="Candidate not found")

    assignments = supabase.table('assignments').select("*").eq('candidate_id', candidate_id).execute()

    try:
        explanation = await asyncio.get_event_loop().run_in_executor(
            executor,
            explain_candidate_with_gpt,
            candidate.data,
            assignments.data
        )

        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")

@router.delete("/{timetable_id}")
async def delete_timetable(timetable_id: str):
    """Delete timetable and all associated data"""
    # Delete assignments first (foreign key constraint)
    supabase.table('assignments').delete().eq('timetable_id', timetable_id).execute()
    # Delete candidates
    supabase.table('candidates').delete().eq('timetable_id', timetable_id).execute()
    # Delete timetable
    result = supabase.table('timetables').delete().eq('id', timetable_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Timetable not found")

    return {"message": "Timetable deleted successfully"}
