import re


def clean_text(text: str) -> str:
    """Lowercase, strip extra whitespace, remove non-ASCII noise."""
    # Remove non-ASCII characters
    text = text.encode("ascii", errors="ignore").decode("ascii")
    # Lowercase
    text = text.lower()
    # Collapse multiple whitespace (spaces, tabs, newlines) into a single space
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_resume(text: str) -> str:
    """clean_text + section header normalization."""
    text = clean_text(text)
    # Normalize common resume section headers to a consistent form
    header_map = {
        r"\b(work experience|professional experience|employment history)\b": "experience",
        r"\b(educational background|education history)\b": "education",
        r"\b(technical skills|core competencies|key skills)\b": "skills",
        r"\b(personal projects|side projects|open.?source)\b": "projects",
        r"\b(certifications?|certificates?)\b": "certifications",
        r"\b(summary of qualifications|professional summary|career objective)\b": "summary",
    }
    for pattern, replacement in header_map.items():
        text = re.sub(pattern, replacement, text)
    return text


def normalize_job_description(text: str) -> str:
    """clean_text + requirement bullet normalization."""
    text = clean_text(text)
    # Normalize bullet/list markers to a uniform dash
    text = re.sub(r"(?m)^\s*[•·▪▸►‣⁃*]\s+", "- ", text)
    # Normalize "required:" / "requirements:" section labels
    text = re.sub(r"\b(requirements?|qualifications?|what you.ll need)\s*:", "requirements:", text)
    # Normalize "responsibilities:" labels
    text = re.sub(r"\b(responsibilities|duties|what you.ll do)\s*:", "responsibilities:", text)
    return text
