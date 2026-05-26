import logging
from datetime import datetime, date

from core.preprocessing import normalize_job_description
from core.embeddings import generate_embedding
from core.skill_extractor import extract_skills
from database.db import supabase

logger = logging.getLogger(__name__)


def create_job(recruiter_id: str, title: str, description: str, deadline) -> dict:
    """
    1. normalize_job_description(description) → clean description
    2. generate_embedding(clean_description) → embedding vector
    3. extract_skills(clean_description) → skills list
    4. Insert into Supabase "jobs" table
    Returns: inserted job record dict
    """
    try:
        clean_description = normalize_job_description(description)
        embedding = generate_embedding(clean_description)
        skills = extract_skills(clean_description)

        deadline_str = deadline.isoformat() if hasattr(deadline, "isoformat") else str(deadline)

        payload = {
            "recruiter_id": recruiter_id,
            "title": title,
            "description": description,
            "embedding": embedding,
            "skills": skills,
            "deadline": deadline_str,
        }

        response = supabase.table("jobs").insert(payload).execute()
        return response.data[0]
    except Exception as e:
        logger.error("Failed to create job: %s", e)
        raise


def get_active_jobs() -> list[dict]:
    """Return jobs where deadline > today, ordered by created_at descending."""
    try:
        today = datetime.now().date().isoformat()
        response = (
            supabase.table("jobs")
            .select("*")
            .gt("deadline", today)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        logger.error("Failed to fetch active jobs: %s", e)
        raise


def get_recruiter_jobs(recruiter_id: str) -> list[dict]:
    """Return all jobs for a given recruiter, ordered by created_at descending."""
    try:
        response = (
            supabase.table("jobs")
            .select("*")
            .eq("recruiter_id", recruiter_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        logger.error("Failed to fetch recruiter jobs for %s: %s", recruiter_id, e)
        raise
