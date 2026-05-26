"""
Tests for auth/password_utils.py
Covers Property 10 and unit cases.
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auth.password_utils import hash_password, verify_password


# ---------------------------------------------------------------------------
# Property 10: Password hashing is non-reversible
# Feature: ai-resume-screening, Property 10
# ---------------------------------------------------------------------------

# Feature: ai-resume-screening, Property 10: Password hashing is non-reversible
@settings(max_examples=100)
@given(
    password=st.text(min_size=1, max_size=50),
    wrong=st.text(min_size=1, max_size=50),
)
def test_password_hashing(password, wrong):
    """Property 10: hash != plaintext, verify(correct) == True, verify(wrong) == False when wrong != password."""
    hashed = hash_password(password)

    # Hash must not equal plaintext
    assert hashed != password

    # Correct password verifies successfully
    assert verify_password(password, hashed) is True

    # Wrong password (when different) must not verify
    if wrong != password:
        assert verify_password(wrong, hashed) is False


# ---------------------------------------------------------------------------
# Unit cases
# ---------------------------------------------------------------------------

def test_hash_password_bcrypt_prefix():
    """hash_password returns a string starting with '$2b$'."""
    hashed = hash_password("mysecretpassword")
    assert hashed.startswith("$2b$")


def test_verify_password_correct():
    """verify_password with correct password returns True."""
    hashed = hash_password("correct_password")
    assert verify_password("correct_password", hashed) is True


def test_verify_password_wrong():
    """verify_password with wrong password returns False."""
    hashed = hash_password("correct_password")
    assert verify_password("wrong_password", hashed) is False
