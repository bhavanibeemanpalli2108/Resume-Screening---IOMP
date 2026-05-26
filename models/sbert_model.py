"""
Thin wrapper — import model from here for backward compatibility.
Actual loading is handled by core.resources (cached_resource).
"""
from core.resources import get_sbert_model

model = get_sbert_model()
