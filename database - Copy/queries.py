from database.db import supabase

def insert_resume(user_id, extracted_text, embedding, file_name, file_path=None, skills=None, experience_years=None, projects=None):
    import json
    response = supabase.table("resumes").upsert({
        "user_id": user_id,
        "extracted_text": extracted_text,
        "embedding": embedding,
        "file_name": file_name,
        "file_path": file_path,
        "skills": skills or [],
        "experience_years": experience_years,
        "projects": json.dumps(projects) if projects is not None else json.dumps([])
    }, on_conflict="user_id").execute()
    return response


def get_user_resume(user_id):
    response = supabase.table("resumes").select("*").eq("user_id", user_id).execute()
    return response.data[0] if response.data else None

def insert_job(recruiter_id, title, description, embedding, skills=None, deadline=None):
    response = supabase.table("jobs").insert({
        "recruiter_id": recruiter_id,
        "title": title,
        "description": description,
        "embedding": embedding,
        "skills": skills or [],
        "deadline": deadline
    }).execute()
    return response


def fetch_all_resumes():
    response = supabase.table("resumes").select("*").execute()
    return response.data

def insert_application(candidate_id, job_id, score, semantic_score=None, skill_score=None, project_score=None, experience_score=None):
    response = supabase.table("applications").insert({
        "candidate_id": candidate_id,
        "job_id": job_id,
        "similarity_score": score,
        "semantic_score": semantic_score,
        "skill_score": skill_score,
        "project_score": project_score,
        "experience_score": experience_score,
        "status": "applied"
    }).execute()
    return response


def update_application_status(candidate_id, job_id, status):
    response = supabase.table("applications").update({
        "status": status
    }).eq("candidate_id", candidate_id).eq("job_id", job_id).execute()
    return response