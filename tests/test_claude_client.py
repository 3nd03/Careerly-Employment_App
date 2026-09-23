import pytest
from unittest.mock import patch, MagicMock
from services.claude_client import call_claude


def make_mock_response(text):
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    return response


@patch("services.claude_client.anthropic.Anthropic")
def test_call_claude_returns_text(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = make_mock_response("Hello from Claude")

    result = call_claude("Say hello")

    assert result == "Hello from Claude"


@patch("services.claude_client.anthropic.Anthropic")
def test_call_claude_passes_prompt(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = make_mock_response("ok")

    call_claude("My prompt here")

    call_args = mock_client.messages.create.call_args
    assert any("My prompt here" in str(m) for m in call_args[1].values() if m)


@patch("services.claude_client.anthropic.Anthropic")
def test_call_claude_passes_system_prompt(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = make_mock_response("ok")

    call_claude("prompt", system="You are a helpful assistant")

    call_args = mock_client.messages.create.call_args
    assert call_args.kwargs.get("system") == "You are a helpful assistant"


@patch("services.claude_client.anthropic.Anthropic")
def test_call_claude_uses_correct_model(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = make_mock_response("ok")

    call_claude("prompt")

    call_args = mock_client.messages.create.call_args
    assert call_args.kwargs.get("model") == "claude-sonnet-4-6"


@patch("services.claude_client.anthropic.Anthropic")
def test_call_claude_raises_on_api_error(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.side_effect = Exception("API unavailable")

    with pytest.raises(Exception, match="API unavailable"):
        call_claude("prompt")
