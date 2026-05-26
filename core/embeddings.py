import streamlit as st
from core.resources import get_sbert_model


@st.cache_data(show_spinner=False, ttl=3600)
def generate_embedding(text: str) -> list:
    """
    Generate a 384-dim embedding, cached per unique text for 1 hour.
    Model is loaded once via cache_resource — never reloaded on page nav.
    """
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text.")
    model = get_sbert_model()
    return model.encode(text).tolist()
