import re
import logging
import numpy as np
import faiss

import config
from core.similarity import cosine_similarity
from core.skill_extractor import extract_years_of_experience
from database.db import supabase

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 5.1 Sub-scorers
# ---------------------------------------------------------------------------

def semantic_score(resume_embedding: list, job_embedding: list) -> float:
    """Cosine similarity between two embeddings. Returns 0.0 if either is None."""
    if resume_embedding is None or job_embedding is None:
        return 0.0
    try:
        return float(cosine_similarity(resume_embedding, job_embedding))
    except Exception as e:
        logger.error("semantic_score error: %s", e)
        return 0.0


def skill_score(resume_skills: list, job_skills: list) -> float:
    """Intersection over job skills. Returns 0.0 if job_skills is empty."""
    if not job_skills:
        return 0.0
    try:
        resume_set = set(s.lower() for s in (resume_skills or []))
        job_set = set(s.lower() for s in job_skills)
        overlap = len(resume_set & job_set)
        return overlap / len(job_set)
    except Exception as e:
        logger.error("skill_score error: %s", e)
        return 0.0


def experience_score(resume_years, job_description: str) -> float:
    """
    Extract required years from job_description via regex.
    Returns min(resume_years / required_years, 1.0) if found,
    0.0 if resume_years is None, or 0.5 (neutral) if not found.
    """
    try:
        match = re.search(r"(\d+)\+?\s+years?", job_description or "", re.IGNORECASE)
        if match:
            required_years = int(match.group(1))
            if required_years == 0:
                return 1.0
            if resume_years is None:
                return 0.0
            return min(float(resume_years) / float(required_years), 1.0)
        return 0.5
    except Exception as e:
        logger.error("experience_score error: %s", e)
        return 0.5


# ---------------------------------------------------------------------------
# 5.2 compute_match
# ---------------------------------------------------------------------------

def compute_match(resume: dict, job: dict) -> dict:
    """
    Compute composite ATS score from all four sub-scores.
    Returns a dict with composite_score and all sub-scores.
    """
    from services.resume_service import score_projects

    try:
        sem = semantic_score(resume.get("embedding"), job.get("embedding"))
        skl = skill_score(resume.get("skills", []), job.get("skills", []))
        proj = score_projects(resume.get("projects", []), job.get("description", ""))
        exp = experience_score(resume.get("experience_years"), job.get("description", ""))

        composite = (
            config.WEIGHT_SEMANTIC * sem
            + config.WEIGHT_SKILL * skl
            + config.WEIGHT_PROJECT * proj
            + config.WEIGHT_EXPERIENCE * exp
        )
        composite = max(0.0, min(1.0, composite))

        return {
            "composite_score": composite,
            "semantic_score": sem,
            "skill_score": skl,
            "project_score": proj,
            "experience_score": exp,
        }
    except Exception as e:
        logger.error("compute_match error: %s", e)
        return {
            "composite_score": 0.0,
            "semantic_score": 0.0,
            "skill_score": 0.0,
            "project_score": 0.0,
            "experience_score": 0.0,
        }


# ---------------------------------------------------------------------------
# 5.3 FAISS functions
# ---------------------------------------------------------------------------

def build_faiss_index(embeddings: list) -> object:
    """
    Build a FAISS IndexFlatIP from a list of 384-dim embeddings.
    Vectors are L2-normalised before insertion so IP == cosine similarity.
    """
    try:
        dim = 384
        index = faiss.IndexFlatIP(dim)
        if not embeddings:
            return index
        vectors = np.array(embeddings, dtype=np.float32)
        # L2-normalise each row
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        vectors = vectors / norms
        index.add(vectors)
        return index
    except Exception as e:
        logger.error("build_faiss_index error: %s", e)
        return faiss.IndexFlatIP(384)


def faiss_top_k(index, job_embedding: list, k: int = 20) -> list:
    """
    Query FAISS index for top-k nearest resume embeddings.
    Returns list of integer indices. Returns [] if index is None or empty.
    """
    try:
        if index is None or index.ntotal == 0:
            return []
        query = np.array([job_embedding], dtype=np.float32)
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm
        actual_k = min(k, index.ntotal)
        _, indices = index.search(query, actual_k)
        return [int(i) for i in indices[0] if i >= 0]
    except Exception as e:
        logger.error("faiss_top_k error: %s", e)
        return []


# ---------------------------------------------------------------------------
# 5.4 rank_candidates
# ---------------------------------------------------------------------------

def rank_candidates(job_id: str) -> list:
    """
    Fetch all applications for job_id ordered by similarity_score DESC.
    Enriches each record with the candidate's email from the users table.
    Returns list of dicts: {candidate_id, email, score, status, application_id}.
    """
    try:
        response = (
            supabase.table("applications")
            .select("id, candidate_id, similarity_score, status")
            .eq("job_id", job_id)
            .order("similarity_score", desc=True)
            .execute()
        )
        applications = response.data or []

        results = []
        for app in applications:
            email = None
            try:
                user_resp = (
                    supabase.table("users")
                    .select("email")
                    .eq("id", app["candidate_id"])
                    .single()
                    .execute()
                )
                email = user_resp.data.get("email") if user_resp.data else None
            except Exception as e:
                logger.warning("Could not fetch email for candidate %s: %s", app.get("candidate_id"), e)

            results.append({
                "candidate_id": app.get("candidate_id"),
                "email": email,
                "score": app.get("similarity_score"),
                "status": app.get("status"),
                "application_id": app.get("id"),
            })

        return results
    except Exception as e:
        logger.error("rank_candidates error: %s", e)
        return []
