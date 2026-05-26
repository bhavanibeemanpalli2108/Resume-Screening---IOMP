"""
Tests for services/matching_service.py
Covers Properties 5, 6, 7, 8, 9 and unit edge cases.
"""
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from hypothesis import given, settings
from hypothesis import strategies as st

import config
from services.matching_service import (
    skill_score,
    experience_score,
    semantic_score,
    build_faiss_index,
    faiss_top_k,
    rank_candidates,
)


# ---------------------------------------------------------------------------
# Property 5: Composite ATS score formula correctness
# Feature: ai-resume-screening, Property 5
# ---------------------------------------------------------------------------

# Feature: ai-resume-screening, Property 5: Composite ATS score formula correctness
@settings(max_examples=100)
@given(
    sem=st.floats(0.0, 1.0, allow_nan=False),
    skl=st.floats(0.0, 1.0, allow_nan=False),
    proj=st.floats(0.0, 1.0, allow_nan=False),
    exp=st.floats(0.0, 1.0, allow_nan=False),
)
def test_composite_score_formula(sem, skl, proj, exp):
    """Property 5: composite = 0.40*sem + 0.30*skl + 0.20*proj + 0.10*exp, always in [0.0, 1.0]."""
    expected = (
        config.WEIGHT_SEMANTIC * sem
        + config.WEIGHT_SKILL * skl
        + config.WEIGHT_PROJECT * proj
        + config.WEIGHT_EXPERIENCE * exp
    )
    expected = max(0.0, min(1.0, expected))
    assert 0.0 <= expected <= 1.0

    # Verify via compute_match with controlled inputs
    resume = {
        "embedding": None,
        "skills": [],
        "projects": [],
        "experience_years": None,
    }
    job = {
        "embedding": None,
        "skills": [],
        "description": "",
    }

    # Patch all sub-scorers to return our controlled values
    with patch("services.matching_service.semantic_score", return_value=sem), \
         patch("services.matching_service.skill_score", return_value=skl), \
         patch("services.resume_service.score_projects", return_value=proj), \
         patch("services.matching_service.experience_score", return_value=exp):
        from services.matching_service import compute_match
        result = compute_match(resume, job)

    composite = result["composite_score"]
    assert 0.0 <= composite <= 1.0
    assert abs(composite - expected) < 1e-9


# ---------------------------------------------------------------------------
# Property 6: Skill score ratio correctness
# Feature: ai-resume-screening, Property 6
# ---------------------------------------------------------------------------

# Feature: ai-resume-screening, Property 6: Skill score ratio correctness
@settings(max_examples=100)
@given(
    resume_skills=st.lists(st.text(min_size=1, max_size=20)),
    job_skills=st.lists(st.text(min_size=1, max_size=20), min_size=1),
)
def test_skill_score_ratio(resume_skills, job_skills):
    """Property 6: skill_score = |intersection| / |job_skills|, always in [0.0, 1.0]."""
    score = skill_score(resume_skills, job_skills)
    assert 0.0 <= score <= 1.0

    resume_set = set(s.lower() for s in resume_skills)
    job_set = set(s.lower() for s in job_skills)
    expected = len(resume_set & job_set) / len(job_set)
    assert abs(score - expected) < 1e-9


# ---------------------------------------------------------------------------
# Property 7: Experience score normalization
# Feature: ai-resume-screening, Property 7
# ---------------------------------------------------------------------------

# Feature: ai-resume-screening, Property 7: Experience score normalization
@settings(max_examples=100)
@given(
    resume_years=st.integers(0, 50),
    required_years=st.integers(1, 20),
)
def test_experience_score_normalization(resume_years, required_years):
    """Property 7: experience_score never exceeds 1.0 for any resume_years >= 0 and required_years > 0."""
    job_description = f"requires {required_years} years experience"
    score = experience_score(resume_years, job_description)
    assert 0.0 <= score <= 1.0
    expected = min(float(resume_years) / float(required_years), 1.0)
    assert abs(score - expected) < 1e-9


# ---------------------------------------------------------------------------
# Property 8: Candidate ranking is sorted descending
# Feature: ai-resume-screening, Property 8
# ---------------------------------------------------------------------------

def test_ranking_sorted_descending():
    """Property 8: rank_candidates result is sorted descending by score."""
    unsorted_apps = [
        {"id": "a1", "candidate_id": "c1", "similarity_score": 0.55, "status": "applied"},
        {"id": "a2", "candidate_id": "c2", "similarity_score": 0.90, "status": "applied"},
        {"id": "a3", "candidate_id": "c3", "similarity_score": 0.72, "status": "applied"},
        {"id": "a4", "candidate_id": "c4", "similarity_score": 0.10, "status": "applied"},
    ]

    mock_app_response = MagicMock()
    mock_app_response.data = unsorted_apps

    mock_user_response = MagicMock()
    mock_user_response.data = {"email": "test@example.com"}

    mock_supabase = MagicMock()
    (mock_supabase.table.return_value
     .select.return_value
     .eq.return_value
     .order.return_value
     .execute.return_value) = mock_app_response

    (mock_supabase.table.return_value
     .select.return_value
     .eq.return_value
     .single.return_value
     .execute.return_value) = mock_user_response

    with patch("services.matching_service.supabase", mock_supabase):
        results = rank_candidates("job-123")

    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True), "Results must be sorted descending by score"


# ---------------------------------------------------------------------------
# Property 9: FAISS top-k matches brute-force cosine
# Feature: ai-resume-screening, Property 9
# ---------------------------------------------------------------------------

def test_faiss_matches_brute_force():
    """Property 9: faiss_top_k matches brute-force cosine ranking for 5 known embeddings."""
    rng = np.random.default_rng(42)
    dim = 384
    embeddings = [rng.random(dim).tolist() for _ in range(5)]
    job_embedding = rng.random(dim).tolist()

    index = build_faiss_index(embeddings)
    faiss_indices = faiss_top_k(index, job_embedding, k=5)

    # Brute-force: L2-normalize then dot product
    emb_arr = np.array(embeddings, dtype=np.float32)
    emb_norms = np.linalg.norm(emb_arr, axis=1, keepdims=True)
    emb_arr = emb_arr / np.where(emb_norms == 0, 1.0, emb_norms)

    job_arr = np.array(job_embedding, dtype=np.float32)
    job_norm = np.linalg.norm(job_arr)
    job_arr = job_arr / (job_norm if job_norm > 0 else 1.0)

    cosines = emb_arr @ job_arr
    brute_force_indices = list(np.argsort(cosines)[::-1])

    assert faiss_indices == brute_force_indices, (
        f"FAISS order {faiss_indices} != brute-force order {brute_force_indices}"
    )


# ---------------------------------------------------------------------------
# Unit edge cases
# ---------------------------------------------------------------------------

def test_skill_score_empty_job_skills():
    """skill_score with empty job_skills returns 0.0."""
    assert skill_score(["python", "java"], []) == 0.0


def test_experience_score_none_resume_years():
    """experience_score with resume_years=None and job_description containing years returns 0.0."""
    assert experience_score(None, "requires 3 years experience") == 0.0


def test_experience_score_no_years_in_description():
    """experience_score with no years in job_description returns 0.5 (neutral)."""
    assert experience_score(5, "great communication skills required") == 0.5


def test_semantic_score_none_embedding():
    """semantic_score with None embedding returns 0.0."""
    assert semantic_score(None, [0.1] * 384) == 0.0
    assert semantic_score([0.1] * 384, None) == 0.0
    assert semantic_score(None, None) == 0.0
