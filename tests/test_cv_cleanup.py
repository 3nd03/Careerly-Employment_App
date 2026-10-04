"""Regression for a tailored-CV bug found during manual testing: when no CV was uploaded, the
profile never carries a real name/email (see prompts/tailored_cv_prompt.py), and despite several
attempts at stronger prompt wording, Claude kept adding a header like "[Candidate Name]\n[Email
Address]" above PERSONAL STATEMENT anyway. Since prompting alone wasn't reliable, this strips it
deterministically instead.
"""
from utils.cv_cleanup import strip_placeholder_cv_header

REAL_OUTPUT_WITH_PLACEHOLDER_HEADER = (
    "[Candidate Name]\nLeeds, UK\n[Email Address] | [Phone Number] | [LinkedIn URL]\n\n\n"
    "PERSONAL STATEMENT\n\nA detail-oriented graduate..."
)


def test_strips_placeholder_header():
    result = strip_placeholder_cv_header(REAL_OUTPUT_WITH_PLACEHOLDER_HEADER)
    assert result.startswith("PERSONAL STATEMENT")
    assert "[" not in result.split("\n\n")[0]


def test_keeps_real_name_header_from_uploaded_cv():
    # When cv_text was provided, the model may legitimately reuse the candidate's real name/email -
    # that has no brackets, so it must not be stripped.
    text = "Alex Taylor\nLeeds, UK\nalex@example.com\n\nPERSONAL STATEMENT\n\nGeography graduate..."
    assert strip_placeholder_cv_header(text) == text


def test_leaves_already_clean_output_untouched():
    text = "PERSONAL STATEMENT\n\nAlready starts correctly."
    assert strip_placeholder_cv_header(text) == text


def test_handles_missing_heading_safely():
    text = "Something that never mentions the heading at all."
    assert strip_placeholder_cv_header(text) == text


def test_handles_empty_string():
    assert strip_placeholder_cv_header("") == ""


def test_does_not_strip_a_plausible_but_unbracketed_header():
    # A header line without brackets looks like real, deliberately-provided content - leave it.
    text = "Jordan Smith - Data Analyst\n\nPERSONAL STATEMENT\n\nBody text."
    assert strip_placeholder_cv_header(text) == text
