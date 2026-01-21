# api/routes/timetables.py
from fastapi import APIRouter, Depends, HTTPException, status
from core.dependencies import get_current_user, supabase
from services.scheduler import TimetableScheduler
from services.ai_orchestrator import extract_metrics, rank_candidates_with_gemini, explain_candidate_with_gpt
import uuid

router = APIRouter(prefix="/api/timetables", tags=["Timetables"], dependencies=[Depends(get_current_user)])

@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
def generate_timetable():
    # Fetch data (same as before)
    teachers = supabase.table('teachers').select("id").execute().data
    # ... fetch all other data ...
    
    scheduler = TimetableScheduler(...)
    solutions = scheduler.solve(solution_limit=5) # Generate up to 5 candidates

    if not solutions:
        raise HTTPException(status_code=500, detail="Could not find any valid solutions.")

    # Create a parent timetable record
    new_timetable = supabase.table('timetables').insert({"term": "Fall 2025"}).execute().data[0]

    # Store each solution as a candidate
    for solution in solutions:
        candidate_id = str(uuid.uuid4())
        metrics = extract_metrics(solution, teachers)
        supabase.table('candidates').insert({
            "id": candidate_id, "timetable_id": new_timetable['id'], "metrics": metrics
        }).execute()
        
        for assignment in solution:
            assignment['candidate_id'] = candidate_id
        supabase.table('assignments').insert(solution).execute()

    return {"message": f"{len(solutions)} candidates are being generated.", "timetable_id": new_timetable['id']}

@router.post("/{timetable_id}/rank", status_code=status.HTTP_200_OK)
def rank_timetable_candidates(timetable_id: uuid.UUID):
    """Ranks the candidates of a given timetable using AI."""
    # Fetch all candidates and their metrics for the timetable
    candidates = supabase.table('candidates').select("id, metrics").eq('timetable_id', str(timetable_id)).execute().data
    if not candidates:
        raise HTTPException(status_code=404, detail="No candidates found for this timetable.")

    # Format for the AI
    candidates_for_ranking = [{"id": c['id'], "metrics": c['metrics']} for c in candidates]
    
    ranking_result = rank_candidates_with_gemini(candidates_for_ranking)
    if not ranking_result or "ranking" not in ranking_result:
        raise HTTPException(status_code=500, detail="Failed to get a valid ranking from AI.")
    
    # Update the 'score' in the database based on the ranking
    ranked_ids = ranking_result['ranking']
    for i, candidate_id in enumerate(ranked_ids):
        score = len(ranked_ids) - i # e.g., 5, 4, 3, 2, 1
        supabase.table('candidates').update({'score': score}).eq('id', candidate_id).execute()
        
    return {"message": "Candidates ranked successfully.", "ranking": ranked_ids}

@router.get("/candidates/{candidate_id}/explain", status_code=status.HTTP_200_OK)
def explain_timetable_candidate(candidate_id: uuid.UUID):
    """Generates an AI explanation for a single candidate."""
    candidate = supabase.table('candidates').select("id, metrics, summary").eq('id', str(candidate_id)).single().execute().data
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    
    # If we already have an explanation, return it
    if candidate.get('summary'):
        return {"explanation": candidate['summary']}
        
    explanation = explain_candidate_with_gpt(candidate['metrics'])
    
    # Save the explanation for future requests
    supabase.table('candidates').update({'summary': explanation}).eq('id', str(candidate_id)).execute()
    
    return {"explanation": explanation}