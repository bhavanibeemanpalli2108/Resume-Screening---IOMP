import re
import logging
import requests
import config

logger = logging.getLogger(__name__)


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
    Use Ollama to generate personalised AI feedback for a candidate.
    Falls back to a rule-based template if Ollama is unavailable.
    """
    try:
        prompt = f"""You are a professional recruitment advisor. Write a concise, constructive, and encouraging feedback message for a job candidate.

Job Title: {job_title}
Outcome: {outcome.upper()}
ATS Match Score: {round(score * 100, 1)}%
Skills Matched: {', '.join(skills_matched) if skills_matched else 'None detected'}
Skills Missing: {', '.join(skills_missing) if skills_missing else 'None'}

Resume Summary (first 800 chars):
{resume_text[:800]}

Job Description Summary (first 500 chars):
{job_description[:500]}

Write 3-4 sentences of personalised feedback:
- If SHORTLISTED: congratulate, mention matched strengths, set expectations for next steps.
- If REJECTED: be kind, mention what was strong, explain the gap, suggest 1-2 specific improvements.

Keep it professional, warm, and specific. Do not use bullet points. Plain paragraph only."""

        response = requests.post(
            config.OLLAMA_BASE_URL + "/api/generate",
            json={"model": config.OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=15,
        )
        if response.status_code == 200:
            text = response.json().get("response", "").strip()
            if text:
                return text
    except Exception as e:
        logger.warning("Ollama feedback generation failed: %s", e)

    # Rule-based fallback
    return _rule_based_feedback(job_title, score, skills_matched, skills_missing, outcome)


def _rule_based_feedback(job_title, score, skills_matched, skills_missing, outcome):
    pct = round(score * 100, 1)
    matched_str = ", ".join(skills_matched[:5]) if skills_matched else "general qualifications"
    missing_str = ", ".join(skills_missing[:3]) if skills_missing else "some required technical areas"

    if outcome == "shortlisted":
        return (
            f"Congratulations on being shortlisted for the {job_title} position! "
            f"Your profile achieved an ATS match score of {pct}%, with strong alignment in {matched_str}. "
            f"Our team was impressed with your background and will be in touch shortly with next steps. "
            f"We look forward to learning more about you."
        )
    else:
        return (
            f"Thank you for applying for the {job_title} position. "
            f"Your profile scored {pct}% on our ATS, showing strengths in {matched_str}. "
            f"However, the role requires stronger coverage in {missing_str}, which affected your overall match. "
            f"We encourage you to build on these areas and apply again in the future — your profile shows real potential."
        )
