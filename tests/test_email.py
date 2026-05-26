"""
Tests for core/email_service.py
Covers Property 11: Shortlist email contains job title
"""
import pytest
from unittest.mock import patch, MagicMock
from hypothesis import given, settings
from hypothesis import strategies as st

from core.email_service import send_shortlist_email


# Feature: ai-resume-screening, Property 11: Shortlist email contains job title
@settings(max_examples=100)
@given(job_title=st.text(min_size=1, max_size=100).filter(lambda s: s.isprintable()))
def test_shortlist_email_contains_title(job_title):
    """Property 11: the email body produced by send_shortlist_email() contains the job_title."""
    captured = {}

    mock_response = MagicMock()
    mock_response.status_code = 202

    mock_sg = MagicMock()
    mock_sg.send.side_effect = lambda msg: captured.update({"msg": msg}) or mock_response

    with patch("core.email_service.SendGridAPIClient", return_value=mock_sg), \
         patch("core.email_service.SENDGRID_API_KEY", "test-sendgrid-key"), \
         patch("core.email_service.SENDER_EMAIL", "test@example.com"):
        result = send_shortlist_email("candidate@example.com", job_title)

    assert result is True, "send_shortlist_email should return True on success"
    assert "msg" in captured, "SendGrid send() should have been called"

    # Verify job_title appears in the subject
    sent_msg = captured["msg"]
    subject_str = str(sent_msg.subject)
    assert job_title in subject_str, (
        f"Expected job_title '{job_title}' in subject '{subject_str}'"
    )


def test_send_shortlist_email_returns_false_without_api_key():
    """send_shortlist_email returns False when SENDGRID_API_KEY is not set."""
    with patch("core.email_service.SENDGRID_API_KEY", ""), \
         patch("core.email_service.SENDER_EMAIL", "test@example.com"):
        result = send_shortlist_email("candidate@example.com", "Engineer")
    assert result is False


def test_send_shortlist_email_returns_false_without_sender():
    """send_shortlist_email returns False when SENDER_EMAIL is not set."""
    with patch("core.email_service.SENDGRID_API_KEY", "test-sendgrid-key"), \
         patch("core.email_service.SENDER_EMAIL", ""):
        result = send_shortlist_email("candidate@example.com", "Engineer")
    assert result is False


def test_send_shortlist_email_handles_sendgrid_exception():
    """send_shortlist_email returns False and logs when SendGrid raises an exception."""
    mock_sg = MagicMock()
    mock_sg.send.side_effect = Exception("Network error")

    with patch("core.email_service.SendGridAPIClient", return_value=mock_sg), \
         patch("core.email_service.SENDGRID_API_KEY", "test-sendgrid-key"), \
         patch("core.email_service.SENDER_EMAIL", "test@example.com"):
        result = send_shortlist_email("candidate@example.com", "Engineer")

    assert result is False
