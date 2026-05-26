"""
Centralized lazy loader for all heavy resources.
All models are loaded ONCE per Streamlit server process using
@st.cache_resource — they survive page navigations and reruns.
"""
import streamlit as st


@st.cache_resource(show_spinner=False)
def get_sbert_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


@st.cache_resource(show_spinner=False)
def get_spacy_nlp():
    import spacy
    return spacy.load("en_core_web_sm")
