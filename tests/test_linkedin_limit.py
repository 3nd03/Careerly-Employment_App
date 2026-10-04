from utils.linkedin_limit import LINKEDIN_CHAR_LIMIT, enforce_limit, trim_to_limit


def test_short_message_unchanged_and_no_retry():
    calls = []
    message = "Hi Sam, I saw your talk on data pipelines. Would you be open to a short call?"
    assert enforce_limit(message, lambda p: calls.append(p) or "") == message
    assert calls == []


def test_long_message_retried_once():
    long_message = "word " * 100
    calls = []

    def fake_claude(prompt):
        calls.append(prompt)
        return "Shorter version. Would you be open to a quick chat?"

    assert enforce_limit(long_message, fake_claude) == "Shorter version. Would you be open to a quick chat?"
    assert len(calls) == 1
    assert "300" in calls[0]


def test_still_too_long_after_retry_is_trimmed():
    result = enforce_limit("x " * 200, lambda prompt: "y " * 200)
    assert len(result) <= LINKEDIN_CHAR_LIMIT


def test_trim_prefers_sentence_boundary():
    first = "I lead backend work on payment systems at a fintech in Leeds. " * 3
    message = first + "Would you be open to a short call next week to talk about the platform team? " * 3
    result = trim_to_limit(message)
    assert len(result) <= LINKEDIN_CHAR_LIMIT
    assert result.endswith((".", "?", "!"))


def test_trim_falls_back_to_word_boundary():
    result = trim_to_limit("averyveryverylongword " * 30)
    assert len(result) <= LINKEDIN_CHAR_LIMIT
    assert result.endswith("...")
    assert "averyveryverylongword..." in result
