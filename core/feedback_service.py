import logging
import config
import re
from core.preprocessing import normalize_resume
from core.skill_extractor import structured_extraction

logger = logging.getLogger(__name__)


def _call_gemini(prompt: str) -> str:
    """Call Gemini API and return text response."""
    try:
        from google import genai
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        logger.error("Gemini API call failed: %s", e)
        return ""


def generate_feedback(
    resume_text: str,
    job_title: str,
    job_description: str,
    score: float,
    skills_matched: list,
    skills_missing: list,
    outcome: str,  # "shortlisted" or "rejected"
) -> str:
    """
    Generate personalised AI feedback using Gemini.
    Falls back to rule-based template if API key missing or call fails.
    """
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "your_gemini_api_key_here":
        return _rule_based_feedback(job_title, score, skills_matched, skills_missing, outcome)

    prompt = f"""You are a professional recruitment advisor. Write concise, constructive, and encouraging feedback for a job candidate.

Job Title: {job_title}
Outcome: {outcome.upper()}
ATS Match Score: {round(score * 100, 1)}%
Skills Matched: {', '.join(skills_matched[:8]) if skills_matched else 'None detected'}
Skills Missing: {', '.join(skills_missing[:5]) if skills_missing else 'None'}

Resume Summary (first 600 chars):
{resume_text[:600]}

Job Description (first 400 chars):
{job_description[:400]}

Write exactly 3-4 sentences of personalised feedback:
- If SHORTLISTED: congratulate warmly, mention 1-2 specific matched strengths, set expectations for next steps.
- If REJECTED: be kind and encouraging, acknowledge what was strong, explain the gap briefly, suggest 1 specific improvement.

Rules: Plain paragraph only. No bullet points. No headers. Be specific, not generic."""

    text = _call_gemini(prompt)
    return text if text else _rule_based_feedback(job_title, score, skills_matched, skills_missing, outcome)


def extract_projects_with_ai(resume_text: str) -> list:
    """
    Robust multi-strategy project extraction from resume text.
    Uses rule-based first, Gemini AI fallback with flexible parsing, and skills enrichment.
    Returns list of {"name": str, "description": str} with tech/skills included.
    """
    text = normalize_resume(resume_text)
    
    # Tier 1: Rule-based
    projects = _rule_based_projects(text)
    if projects:
        return _enrich_projects_with_skills(projects)
    
    # Tier 2: AI if key available
    if config.GEMINI_API_KEY and config.GEMINI_API_KEY != "your_gemini_api_key_here":
        prompt = f'''Identify all projects, personal projects, side projects, or notable built items from the resume text.
Handle varying formats: bullets, experience sections, inline mentions.
For each, provide:
- "name": Short project title (infer if not explicit, e.g. first few words)
- "description": 1-2 sentences on what was built + key tech/skills used (extract even if not listed explicitly)

Return ONLY valid JSON array like: [{{"name": "Project X", "description": "Built Y using Z, A, B."}}]
If none found, [].

Resume:
{{text[:4000]}}'''

        raw_response = _call_gemini(prompt)
        if raw_response:
            projects = _lenient_parse_projects(raw_response)
            if projects:
                return _enrich_projects_with_skills(projects)
    
    # Final fallback
    return _enrich_projects_with_skills([])


def _lenient_parse_projects(raw: str) -> list:
    """Try multiple ways to extract valid JSON list from AI response."""
    import json
    candidates = [
        raw.strip(),
        re.search(r"\\[\\s*\\[.*?\\]\\s*\\]", raw, re.DOTALL),
        re.search(r"\\[.*?\\]", raw, re.DOTALL),
    ]
    for cand in candidates:
        if isinstance(cand, str):
            try:
                parsed = json.loads(cand)
                if isinstance(parsed, list):
                    return [
                        {"name": str(p.get("name", "")).strip(), "description": str(p.get("description", "")).strip()}
                        for p in parsed 
                        if isinstance(p, dict) and p.get("name", "").strip()
                    ]
            except json.JSONDecodeError:
                continue
    logger.warning("All parsing attempts failed for projects")
    return []


def _enrich_projects_with_skills(projects: list) -> list:
    """Append top skills to descriptions."""
    for p in projects:
        if p.get("description"):
            extracted = structured_extraction(p["description"])
            skills = extracted.get("skills", [])[:3]
            if skills:
                p["description"] += f" (Tech/Skills: {', '.join(skills)})"
    return projects


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
    bullets = re.findall(r"(?m)^[ -*]\\s*(.+)$", section_text)
    for bullet in bullets:
        bullet = bullet.strip()
        if len(bullet) > 10:
            words = bullet.split()
            name = " ".join(words[:5]) if len(words) >= 5 else bullet
            projects.append({"name": name, "description": bullet})
    return projects


def _rule_based_feedback(job_title, score, skills_matched, skills_missing, outcome):
    pct = round(score * 100, 1)
    matched_str = ", ".join(skills_matched[:4]) if skills_matched else "your general qualifications"
    missing_str = ", ".join(skills_missing[:3]) if skills_missing else "some required technical areas"

    if outcome == "shortlisted":
        return (
            f"Congratulations on being shortlisted for the {job_title} position! "
            f"Your profile achieved an ATS match score of {pct}%, with strong alignment in {matched_str}. "
            f"Our team was impressed with your background and will be in touch shortly with next steps."
        )
    else:
        return (
            f"Thank you for applying for the {job_title} position. "
            f"Your profile scored {pct}% on our ATS, showing strengths in {matched_str}. "
            f"However, the role requires stronger coverage in {missing_str}, which affected your overall match. "
            f"We encourage you to build on these areas and apply again — your profile shows real potential."
        )
