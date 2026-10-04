import httpx
import pytest

from services import email_service
from services.email_service import send_email, send_password_reset_email


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ["RESEND_API_KEY", "EMAIL_FROM", "EMAIL_BACKEND", "FRONTEND_URL"]:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def fake_post(monkeypatch):
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return httpx.Response(200, json={"id": "email_123"}, request=httpx.Request("POST", url))

    monkeypatch.setattr(email_service.httpx, "post", post)
    return calls


def test_sends_via_resend_when_key_set(monkeypatch, fake_post):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("EMAIL_FROM", "Careerly <no-reply@example.com>")

    assert send_email("user@example.com", "Hi", "text body", "<p>html</p>") is True

    url, kwargs = fake_post[0]
    assert url == "https://api.resend.com/emails"
    assert kwargs["headers"]["Authorization"] == "Bearer re_test"
    assert kwargs["json"] == {
        "from": "Careerly <no-reply@example.com>",
        "to": ["user@example.com"],
        "subject": "Hi",
        "text": "text body",
        "html": "<p>html</p>",
    }


def test_resend_error_returns_false_without_raising(monkeypatch, caplog):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setattr(
        email_service.httpx,
        "post",
        lambda url, **kw: httpx.Response(403, text="domain not verified", request=httpx.Request("POST", url)),
    )

    assert send_email("user@example.com", "Hi", "text", "<p>html</p>") is False
    assert "domain not verified" in caplog.text


def test_network_error_returns_false(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")

    def boom(url, **kw):
        raise httpx.ConnectError("no network")

    monkeypatch.setattr(email_service.httpx, "post", boom)
    assert send_email("user@example.com", "Hi", "text", "<p>html</p>") is False


def test_console_backend_logs_instead_of_sending(monkeypatch, fake_post, caplog):
    monkeypatch.setenv("EMAIL_BACKEND", "console")
    assert send_email("user@example.com", "Hi", "the body", "<p>html</p>") is True
    assert fake_post == []
    assert "the body" in caplog.text


def test_not_configured_logs_error(fake_post, caplog):
    assert send_email("user@example.com", "Hi", "text", "<p>html</p>") is False
    assert fake_post == []
    assert "email not configured" in caplog.text


def test_reset_email_contains_link_to_frontend(monkeypatch, fake_post):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("FRONTEND_URL", "https://careerly.example.com/")

    send_password_reset_email("user@example.com", "tok_abc-123")

    body = fake_post[0][1]["json"]
    link = "https://careerly.example.com/reset-password?token=tok_abc-123"
    assert link in body["text"]
    assert f'href="{link}"' in body["html"]
    assert "1 hour" in body["text"]


def test_reset_link_defaults_to_local_frontend(monkeypatch, fake_post):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    send_password_reset_email("user@example.com", "tok")
    assert "http://localhost:3000/reset-password?token=tok" in fake_post[0][1]["json"]["text"]
