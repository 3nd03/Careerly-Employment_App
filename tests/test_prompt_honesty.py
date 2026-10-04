"""Guards against two issues found during manual testing of real Claude output:

1. Cover letters included placeholder brackets like [Your Name] / [Your Address] because the
   model defaulted to a formal letter header the profile has no data for.
2. Both the cover letter and tailored CV sometimes overstated a skill the candidate described as
   basic/limited (e.g. "basic SQL" became "I write SQL joins regularly"), or implied familiarity
   with a tool from the job description that was never in the candidate's profile.

These tests only check the prompt text asks the model not to do these things; they can't verify
the model actually complies (see tests/claude_tools.py-style manual checks for that), but they
catch someone accidentally deleting the instruction while editing the prompt.
"""
from prompts.cover_letter_prompt import build_cover_letter_prompt
from prompts.tailored_cv_prompt import build_tailored_cv_prompt

PROFILE = {"target_role": "Engineer", "current_skills": "basic SQL"}


def test_cover_letter_prompt_forbids_placeholder_brackets():
    prompt = build_cover_letter_prompt(PROFILE, "Job description", "Formal")
    assert "[Your Name]" in prompt  # named as a forbidden example
    assert "placeholder brackets" in prompt


def test_cover_letter_prompt_forbids_skill_inflation():
    prompt = build_cover_letter_prompt(PROFILE, "Job description", "Formal")
    assert "do not inflate them" in prompt
    assert "basic" in prompt and "limited" in prompt


def test_tailored_cv_prompt_forbids_skill_inflation():
    prompt = build_tailored_cv_prompt(PROFILE, "Job description")
    assert "Do not claim experience, familiarity, or proficiency with a specific tool" in prompt
    assert "basic" in prompt and "limited" in prompt


def test_tailored_cv_prompt_discourages_placeholder_contact_header():
    # Without an uploaded CV, the profile never carries a real name/phone/email (see CANDIDATE
    # PROFILE fields above), so the model tends to invent a "[Candidate Name]" header anyway.
    # This prompt wording didn't reliably stop it in manual testing (see utils/cv_cleanup.py,
    # which strips it deterministically), but it's still worth keeping as a best-effort nudge.
    prompt = build_tailored_cv_prompt(PROFILE, "Job description")
    assert "[Candidate Name]" in prompt  # named as a forbidden example
    assert 'begin with the exact heading "PERSONAL STATEMENT"' in prompt
