# import os
# from dotenv import load_dotenv

# load_dotenv()

# # Supabase
# SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
# SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

# # Email (SendGrid)
# SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
# SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "")

# # Gemini AI (replaces Ollama)
# GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
# GEMINI_MODEL: str = "gemini-2.0-flash"

import os

try:
    import streamlit as st

    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    SENDGRID_API_KEY = st.secrets["SENDGRID_API_KEY"]
    SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

except:
    from dotenv import load_dotenv

    load_dotenv()

    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Embedding
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
FAISS_INDEX_PATH: str = "faiss_index.bin"

# ATS scoring weights
WEIGHT_SEMANTIC: float = 0.40
WEIGHT_SKILL: float = 0.30
WEIGHT_PROJECT: float = 0.20
WEIGHT_EXPERIENCE: float = 0.10

# Scoring thresholds
SHORTLIST_THRESHOLD: float = 0.65
MAX_EXPERIENCE_YEARS: int = 20
