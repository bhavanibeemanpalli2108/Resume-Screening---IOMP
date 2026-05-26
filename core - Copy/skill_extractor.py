import re
import spacy
from utils.constants import SKILL_LIST

nlp = spacy.load("en_core_web_sm")

def extract_email(text):
    pattern = r"[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+"
    match = re.search(pattern, text)
    return match.group() if match else None

def extract_phone(text):
    pattern = r"\+?\d[\d -]{8,}\d"
    match = re.search(pattern, text)
    return match.group() if match else None

def extract_skills(text):
    text_lower = text.lower()
    found_skills = []

    for skill in SKILL_LIST:
        if skill.lower() in text_lower:
            found_skills.append(skill)

    return list(set(found_skills))

def extract_entities(text):
    doc = nlp(text)

    education = []
    organizations = []

    for ent in doc.ents:
        if ent.label_ == "ORG":
            organizations.append(ent.text)
        if ent.label_ in ["EDUCATION", "ORG"]:
            education.append(ent.text)

    return {
        "organizations": list(set(organizations)),
        "education": list(set(education))
    }

def extract_years_of_experience(text):
    pattern = r"(\d+)\s+years?"
    matches = re.findall(pattern, text)
    if matches:
        return max([int(x) for x in matches])
    return None

def structured_extraction(text):
    return {
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "experience_years": extract_years_of_experience(text),
        "entities": extract_entities(text)
    }