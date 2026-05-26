from core.similarity import cosine_similarity
from config import WEIGHT_SEMANTIC, WEIGHT_SKILL, WEIGHT_PROJECT, WEIGHT_EXPERIENCE

def skill_overlap_score(resume_skills, job_skills):
    if not resume_skills or not job_skills:
        return 0

    overlap = set(resume_skills).intersection(set(job_skills))
    return len(overlap) / len(job_skills)

def final_score(resume_embedding, job_embedding, resume_skills, job_skills,
                project_score: float = 0.0, experience_score: float = 0.0):

    if resume_embedding is None or job_embedding is None:
        return 0

    semantic_score = cosine_similarity(resume_embedding, job_embedding)
    skill_score = skill_overlap_score(resume_skills, job_skills)

    score = (
        WEIGHT_SEMANTIC * semantic_score +
        WEIGHT_SKILL * skill_score +
        WEIGHT_PROJECT * project_score +
        WEIGHT_EXPERIENCE * experience_score
    )

    return float(max(0.0, min(1.0, score)))
