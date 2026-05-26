import re
import json
import logging
import requests

import config
from core.parser import parse_resume
from core.preprocessing import normalize_resume
from core.skill_extractor import structured_extraction
from core.embeddings import generate_embedding
from core.similarity import cosine_similarity
from database.db import supabase
from database.queries import get_user_resume

logger = logging.getLogger(__name__)


def _rule_based_projects(text):
    projects = []
    section_match = re.search(
        r"(?im)^(projects?|personal projects?|side projects?|open.?source)\s*[:\-]?\s*$",
        text,
    )
    if not section_match:
        return projects
    section_start = section_match.end()
    section_text = text[section_start:section_start + 2000]
    next_section = re.search(r"(?im)^[A-Z][A-Za-z ]{2,30}\s*[:\-]?\s*$", section_text)
    if next_section:
        section_text = section_text[: next_section.start()]
    bullets = re.findall(r"(?m)^[\s\-*]\s*(.+)$", section_text)
    for bullet in bullets:
        bullet = bullet.strip()
        if len(bullet) > 10:
            words = bullet.split()
            name = " ".join(words[:5]) if len(words) >= 5 else bullet
            projects.append({"name": name, "description": bullet})
    return projects


def extract_projects(text):
    projects = _rule_based_projects(text)
    if projects:
        return projects
    try:
        prompt = (
            "Extract all projects from the following resume text. "
            "Return a JSON array of objects with keys 'name' and 'description'. "
            "Only return the JSON array, nothing else.\n\n" + text[:3000]
        )
        response = requests.post(
            config.OLLAMA_BASE_URL + "/api/generate",
            json={"model": config.OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=5,
        )
        if response.status_code == 200:
            raw = response.json().get("response", "")
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                if isinstance(parsed, list):
                    return [
                        {"name": str(p.get("name", "")), "description": str(p.get("description", ""))}
                        for p in parsed if isinstance(p, dict)
                    ]
    except Exception as e:
        logger.warning("Ollama project extraction failed: %s", e)
    return projects


def score_projects(resume_projects, job_description):
    if not resume_projects or not job_description:
        return 0.0
    try:
        job_embedding = generate_embedding(job_description)
        similarities = []
        for project in resume_projects:
            desc = project.get("description", "")
            if desc:
                proj_embedding = generate_embedding(desc)
                sim = cosine_similarity(proj_embedding, job_embedding)
                similarities.append(sim)
        return float(sum(similarities) / len(similarities)) if similarities else 0.0
    except Exception as e:
        logger.error("score_projects error: %s", e)
        return 0.0


def process_resume(uploaded_file, user_id):
    try:
        raw_text = parse_resume(uploaded_file)
        if not raw_text:
            logger.error("Failed to parse resume for user %s", user_id)
            return {}
        clean_text = normalize_resume(raw_text)
        extracted = structured_extraction(clean_text)
        skills = extracted.get("skills", [])
        experience_years = extracted.get("experience_years")
        projects = extract_projects(clean_text)
        embedding = generate_embedding(clean_text)
        file_path = f"{user_id}_{uploaded_file.name}"
        try:
            supabase.storage.from_("resumes").upload(
                file_path, uploaded_file.getvalue(), {"upsert": "true"}
            )
        except Exception as e:
            logger.warning("Storage upload failed: %s", e)
        resume_data = {
            "extracted_text": raw_text,
            "embedding": embedding,
            "file_name": uploaded_file.name,
            "file_path": file_path,
            "skills": skills,
            "experience_years": experience_years,
            "projects": projects,
        }
        existing = get_user_resume(user_id)
        if existing:
            supabase.table("resumes").update(resume_data).eq("user_id", user_id).execute()
        else:
            resume_data["user_id"] = user_id
            supabase.table("resumes").insert(resume_data).execute()
        resume_data["user_id"] = user_id
        return resume_data
    except Exception as e:
        logger.error("process_resume error for user %s: %s", user_id, e)
        return {}
