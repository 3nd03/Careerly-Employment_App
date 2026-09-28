REQUIRED_SECTIONS = [
    "PERSONAL STATEMENT",
    "KEY SKILLS",
    "WORK EXPERIENCE",
    "EDUCATION",
    "ADDITIONAL INFORMATION",
]

DISALLOWED_CHARACTERS = ["|", "*", "_", "#", "`", "~", "•", "◦", "▪", "—", "–", "☐", "☑"]


def check_ats_compatibility(cv_text: str) -> bool:
    upper_text = cv_text.upper()
    if not all(section in upper_text for section in REQUIRED_SECTIONS):
        return False
    if any(char in cv_text for char in DISALLOWED_CHARACTERS):
        return False
    if "![" in cv_text or "<img" in cv_text.lower() or "<table" in cv_text.lower():
        return False
    return True
