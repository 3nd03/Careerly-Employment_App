import re
from typing import Callable

LINKEDIN_CHAR_LIMIT = 300


def build_shorten_prompt(message: str, limit: int = LINKEDIN_CHAR_LIMIT) -> str:
    return (
        f"This LinkedIn connection note is {len(message)} characters, but the hard limit is {limit} "
        f"characters including spaces. Rewrite it to at most {limit - 20} characters, keeping the "
        "specific reason for reaching out and the closing ask. UK English, no em dashes. "
        f"Return only the message.\n\n{message}"
    )


def trim_to_limit(message: str, limit: int = LINKEDIN_CHAR_LIMIT) -> str:
    """Cut at the last sentence end that fits, falling back to the last whole word."""
    message = message.strip()
    if len(message) <= limit:
        return message
    head = message[:limit]
    sentence_ends = [m.end() for m in re.finditer(r"[.!?](?=\s|$)", head)]
    if sentence_ends and sentence_ends[-1] >= limit // 2:
        return head[:sentence_ends[-1]].strip()
    return head[:limit - 3].rsplit(" ", 1)[0].rstrip(" ,;:") + "..."


def enforce_limit(message: str, call_claude: Callable[[str], str], limit: int = LINKEDIN_CHAR_LIMIT) -> str:
    """Ask Claude to shorten an over-limit message once, then trim whatever is still too long."""
    message = message.strip()
    if len(message) <= limit:
        return message
    return trim_to_limit(call_claude(build_shorten_prompt(message, limit)), limit)
