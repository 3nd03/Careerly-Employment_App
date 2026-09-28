from utils.ats_check import check_ats_compatibility

VALID_CV = """PERSONAL STATEMENT
A motivated candidate.

KEY SKILLS
- Python
- SQL

WORK EXPERIENCE
- Backend developer, 2020 to present

EDUCATION
- BSc Computer Science

ADDITIONAL INFORMATION
- Available immediately
"""


def test_valid_cv_passes():
    assert check_ats_compatibility(VALID_CV) is True


def test_missing_section_fails():
    cv = VALID_CV.replace("EDUCATION\n- BSc Computer Science\n\n", "")
    assert check_ats_compatibility(cv) is False


def test_markdown_symbols_fail():
    cv = VALID_CV.replace("- Python", "**Python**")
    assert check_ats_compatibility(cv) is False


def test_table_pipe_character_fails():
    cv = VALID_CV + "\n| Column A | Column B |"
    assert check_ats_compatibility(cv) is False
