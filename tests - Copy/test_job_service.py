"""
Tests for services/job_service.py
Covers Property 12.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from services.job_service import get_active_jobs


# ---------------------------------------------------------------------------
# Property 12: Expired jobs excluded from active listing
# Feature: ai-resume-screening, Property 12
# ---------------------------------------------------------------------------

def test_expired_jobs_excluded():
    """Property 12: get_active_jobs() returns only jobs with deadline > today.

    Since get_active_jobs delegates filtering to Supabase .gt("deadline", today),
    we verify that the correct filter is applied and that only the data returned
    by Supabase (which would already be filtered server-side) is passed through.
    """
    today = date.today()
    future_jobs = [
        {"id": "j1", "title": "Engineer", "deadline": (today + timedelta(days=5)).isoformat()},
        {"id": "j2", "title": "Designer", "deadline": (today + timedelta(days=1)).isoformat()},
    ]

    mock_response = MagicMock()
    mock_response.data = future_jobs

    mock_chain = MagicMock()
    mock_chain.execute.return_value = mock_response

    mock_supabase = MagicMock()
    (mock_supabase.table.return_value
     .select.return_value
     .gt.return_value
     .order.return_value) = mock_chain

    with patch("services.job_service.supabase", mock_supabase):
        results = get_active_jobs()

    # Verify the .gt filter was called with "deadline" and today's ISO date
    gt_call = mock_supabase.table.return_value.select.return_value.gt
    gt_call.assert_called_once_with("deadline", today.isoformat())

    # Verify only the future jobs are returned
    assert results == future_jobs
    assert len(results) == 2


def test_get_active_jobs_returns_empty_when_all_expired():
    """get_active_jobs returns an empty list when Supabase returns no results."""
    mock_response = MagicMock()
    mock_response.data = []

    mock_chain = MagicMock()
    mock_chain.execute.return_value = mock_response

    mock_supabase = MagicMock()
    (mock_supabase.table.return_value
     .select.return_value
     .gt.return_value
     .order.return_value) = mock_chain

    with patch("services.job_service.supabase", mock_supabase):
        results = get_active_jobs()

    assert results == []
