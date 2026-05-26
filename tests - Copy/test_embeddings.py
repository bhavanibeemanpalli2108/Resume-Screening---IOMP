"""
Tests for core/embeddings.py
Covers Property 3.
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from core.embeddings import generate_embedding


# ---------------------------------------------------------------------------
# Property 3: Embedding dimension invariant
# Feature: ai-resume-screening, Property 3
# ---------------------------------------------------------------------------

# Feature: ai-resume-screening, Property 3: Embedding dimension invariant
@settings(max_examples=5)
@given(text=st.text(min_size=1, max_size=500))
def test_embedding_dimension(text):
    """Property 3: generate_embedding(text) always returns a list of exactly 384 floats."""
    result = generate_embedding(text)
    assert isinstance(result, list), "Embedding must be a list"
    assert len(result) == 384, f"Expected 384 dimensions, got {len(result)}"
    assert all(isinstance(v, float) for v in result), "All embedding values must be floats"
