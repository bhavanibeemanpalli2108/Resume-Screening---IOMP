import re
from core.resources import get_spacy_nlp

# ---------------------------------------------------------------
# Curated seed list — used as a fallback anchor, not a hard limit
# ---------------------------------------------------------------
SEED_SKILLS = {
    # Languages
    "python", "java", "c++", "c#", "c", "go", "rust", "kotlin", "swift",
    "typescript", "javascript", "ruby", "php", "scala", "r", "matlab",
    "bash", "shell", "perl", "dart", "lua",
    # Web
    "html", "css", "react", "angular", "vue", "nextjs", "nodejs", "express",
    "django", "flask", "fastapi", "spring", "laravel", "rails", "graphql",
    "rest", "restful", "websocket", "tailwind", "bootstrap",
    # Data / ML / AI
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "keras", "scikit-learn", "xgboost", "lightgbm",
    "hugging face", "transformers", "bert", "gpt", "llm", "rag",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
    "data analysis", "data science", "feature engineering", "model deployment",
    "mlops", "airflow", "mlflow", "kubeflow",
    # Databases
    "sql", "mysql", "postgresql", "sqlite", "mongodb", "redis", "cassandra",
    "elasticsearch", "neo4j", "dynamodb", "firebase", "supabase",
    # Cloud / DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
    "ansible", "jenkins", "github actions", "ci/cd", "linux", "unix",
    "nginx", "apache", "serverless",
    # Tools
    "git", "github", "gitlab", "jira", "confluence", "figma", "postman",
    "swagger", "vscode", "jupyter", "colab",
    # Concepts
    "agile", "scrum", "microservices", "system design", "oop",
    "data structures", "algorithms", "api", "oauth", "jwt",
    "blockchain", "cybersecurity", "networking",
}

# Patterns that indicate a skill context in text
_SKILL_CONTEXT_PATTERNS = [
    r"(?:proficient|experienced|skilled|expertise|knowledge|familiar|worked with|using|used|built with|developed with)\s+(?:in\s+)?([A-Za-z0-9+#.\-/ ]{2,40})",
    r"(?:technologies|tools|stack|languages|frameworks|libraries)\s*[:\-]\s*([A-Za-z0-9+#.,\-/ ]{3,120})",
    r"(?:skills?)\s*[:\-]\s*([A-Za-z0-9+#.,\-/ ]{3,120})",
]


def extract_skills(text: str) -> list:
    """
    Extract skills using three complementary strategies:
    1. Seed list matching (fast, high precision)
    2. spaCy NER + noun chunk extraction (catches unlisted tech terms)
    3. Regex context patterns (catches inline skill mentions)

    Returns a deduplicated, sorted list of skill strings.
    """
    found = set()
    text_lower = text.lower()

    # --- Strategy 1: Seed list ---
    for skill in SEED_SKILLS:
        # Use word-boundary-aware matching for short skills to avoid false positives
        if len(skill) <= 3:
            if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
                found.add(skill)
        else:
            if skill in text_lower:
                found.add(skill)

    # --- Strategy 2: spaCy noun chunks (tech terms not in seed list) ---
    doc = get_spacy_nlp()(text[:5000])  # model loaded from cache
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.strip().lower()
        # Keep chunks that look like tech terms: short, no common words
        if 2 <= len(chunk_text.split()) <= 4 and _looks_like_skill(chunk_text):
            found.add(chunk_text)

    # Also check named entities
    for ent in doc.ents:
        if ent.label_ in ("ORG", "PRODUCT", "WORK_OF_ART"):
            ent_text = ent.text.strip().lower()
            if _looks_like_skill(ent_text):
                found.add(ent_text)

    # --- Strategy 3: Regex context patterns ---
    for pattern in _SKILL_CONTEXT_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            raw = match.group(1)
            # Split on commas, slashes, bullets
            parts = re.split(r"[,/|•·]", raw)
            for part in parts:
                part = part.strip().strip(".")
                if 2 <= len(part) <= 40 and _looks_like_skill(part):
                    found.add(part)

    # Clean up: remove overly generic or stopword-only entries
    cleaned = {s for s in found if _is_valid_skill(s)}
    return sorted(cleaned)


def _looks_like_skill(text: str) -> bool:
    """Heuristic: skill-like strings contain alphanumeric chars, not pure stopwords."""
    stopwords = {
        "the", "and", "for", "with", "that", "this", "from", "have",
        "been", "will", "are", "was", "our", "your", "their", "which",
        "also", "more", "some", "such", "other", "into", "about",
        "experience", "knowledge", "ability", "skills", "work", "team",
        "using", "used", "good", "strong", "excellent", "various",
    }
    words = text.lower().split()
    if not words:
        return False
    if all(w in stopwords for w in words):
        return False
    if re.match(r"^\d+$", text):
        return False
    return bool(re.search(r"[a-zA-Z]", text))


def _is_valid_skill(skill: str) -> bool:
    if len(skill) < 2 or len(skill) > 50:
        return False
    # Must contain at least one letter
    if not re.search(r"[a-zA-Z]", skill):
        return False
    return True


def extract_email(text: str) -> str | None:
    match = re.search(r"[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+", text)
    return match.group() if match else None


def extract_phone(text: str) -> str | None:
    match = re.search(r"\+?\d[\d -]{8,}\d", text)
    return match.group() if match else None


def extract_years_of_experience(text: str) -> int | None:
    matches = re.findall(r"(\d+)\s+years?", text, re.IGNORECASE)
    return max(int(x) for x in matches) if matches else None


def extract_entities(text: str) -> dict:
    doc = get_spacy_nlp()(text[:5000])
    orgs, edu = [], []
    for ent in doc.ents:
        if ent.label_ == "ORG":
            orgs.append(ent.text)
        if ent.label_ in ("EDUCATION", "ORG"):
            edu.append(ent.text)
    return {
        "organizations": list(set(orgs)),
        "education": list(set(edu)),
    }


def structured_extraction(text: str) -> dict:
    return {
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "experience_years": extract_years_of_experience(text),
        "entities": extract_entities(text),
    }
