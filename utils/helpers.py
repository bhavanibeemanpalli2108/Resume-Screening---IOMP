from datetime import datetime


def format_score(score: float) -> str:
    """Format a float score as a percentage string, e.g. 0.85 → '85.0%'."""
    return f"{round(score * 100, 1)}%"


def is_deadline_active(deadline_str: str) -> bool:
    """Return True if the deadline ISO string is in the future."""
    try:
        deadline = datetime.fromisoformat(deadline_str)
        return deadline > datetime.now()
    except Exception:
        return False


def truncate(text: str, max_len: int = 200) -> str:
    """Truncate text to max_len characters, appending '...' if truncated."""
    if not text:
        return ""
    return text[:max_len] + "..." if len(text) > max_len else text
