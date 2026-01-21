# services/ai_orchestrator.py
import os
import google.generativeai as genai
from openai import OpenAI
import json
import statistics

# --- Metric Extraction ---
def extract_metrics(solution, teachers):
    """Calculates key metrics for a given timetable solution."""
    teacher_load = {t['id']: 0 for t in teachers}
    for assignment in solution:
        teacher_load[assignment['teacher_id']] += 1
    
    # Fairness: Lower standard deviation is better (more balanced load)
    load_values = [v for v in teacher_load.values() if v > 0]
    fairness = statistics.stdev(load_values) if len(load_values) > 1 else 0

    return {
        "total_periods_scheduled": len(solution),
        "teacher_workload_stdev": round(fairness, 2),
        "teachers_used": len(load_values)
    }

# --- AI Integration ---
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def rank_candidates_with_gemini(candidates_with_metrics: list):
    """Uses Gemini to rank timetable candidates."""
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    You are an expert school administrator. Your task is to rank timetable candidates based on quality.
    A good timetable has a low "teacher_workload_stdev" (meaning work is distributed fairly) and uses a reasonable number of teachers.
    
    Here are the candidates and their metrics in JSON format:
    {json.dumps(candidates_with_metrics, indent=2)}

    Please respond with ONLY a JSON object containing a single key "ranking" which is an array of the candidate IDs, ordered from best to worst.
    Example response: {{"ranking": ["c_id_1", "c_id_3", "c_id_2"]}}
    """
    
    response = model.generate_content(prompt)
    try:
        # Clean up the response to ensure it's valid JSON
        cleaned_response = response.text.strip().replace('`', '').replace('json', '')
        return json.loads(cleaned_response)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing Gemini response: {e}")
        return None

def explain_candidate_with_gpt(metrics: dict):
    """Uses GPT to generate a natural language explanation of a timetable."""
    prompt = f"""
    You are a helpful school principal explaining the quality of a generated timetable to an administrator.
    Based on the following metrics, provide a short, easy-to-understand summary (2-3 sentences).
    - A low teacher workload standard deviation is very good (fair).
    - A high number of teachers used might be inefficient.
    
    Metrics: {json.dumps(metrics, indent=2)}
    
    Provide a concise explanation.
    """
    
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    return response.choices[0].message.content