import re

PERSONAL_STATEMENT_HEADING = "PERSONAL STATEMENT"
# A bracketed placeholder like [Candidate Name] or [Start Date]. Real contact details (an actual
# name, email, etc. the model copied from an uploaded CV) never contain brackets, so this only
# matches the case we want to strip.
PLACEHOLDER_PATTERN = re.compile(r"\[[^\[\]\n]{1,40}\]")


def strip_placeholder_cv_header(cv_text: str) -> str:
    """Tailored CVs should start with PERSONAL STATEMENT (see prompts/tailored_cv_prompt.py), but
    the model sometimes adds a contact header above it anyway, and when there's no uploaded CV to
    draw a real name/email from it falls back to placeholders like "[Candidate Name]". Prompting
    alone didn't reliably stop this, so this removes that header deterministically: a genuine
    header carried over from a real uploaded CV has no brackets and is left untouched.
    """
    idx = cv_text.upper().find(PERSONAL_STATEMENT_HEADING)
    if idx <= 0:
        return cv_text
    header = cv_text[:idx]
    if PLACEHOLDER_PATTERN.search(header):
        return cv_text[idx:].lstrip()
    return cv_text
