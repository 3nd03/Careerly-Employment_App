"""Transactional email. Sends via Resend when RESEND_API_KEY is set; EMAIL_BACKEND=console logs instead (local dev)."""
import html
import logging
import os

import httpx

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"
DEFAULT_FRONTEND_URL = "http://localhost:3000"  # vite.config.js dev server port


def frontend_url() -> str:
    return (os.getenv("FRONTEND_URL") or DEFAULT_FRONTEND_URL).rstrip("/")


def send_email(to: str, subject: str, text: str, html_body: str) -> bool:
    """Returns True if the email was handed off. Never raises: callers must not leak failures to users."""
    api_key = os.getenv("RESEND_API_KEY")
    if api_key:
        try:
            response = httpx.post(
                RESEND_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "from": os.getenv("EMAIL_FROM", ""),
                    "to": [to],
                    "subject": subject,
                    "text": text,
                    "html": html_body,
                },
                timeout=10,
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            detail = e.response.text[:200] if isinstance(e, httpx.HTTPStatusError) else str(e)
            logger.error("email send failed: to=%s subject=%r error=%s", to, subject, detail)
            return False

    if os.getenv("EMAIL_BACKEND", "").lower() == "console":
        logger.warning("EMAIL (console backend) to=%s subject=%r\n%s", to, subject, text)
        return True

    logger.error("email not configured (set RESEND_API_KEY, or EMAIL_BACKEND=console for local dev); not sent to %s", to)
    return False


def send_password_reset_email(to: str, token: str) -> bool:
    link = f"{frontend_url()}/reset-password?token={token}"
    text = (
        "Someone asked to reset the password for your Careerly account.\n\n"
        f"Reset it here (the link works once and expires in 1 hour):\n{link}\n\n"
        "If you didn't ask for this, you can ignore this email; your password won't change."
    )
    safe_link = html.escape(link, quote=True)
    html_body = (
        "<p>Someone asked to reset the password for your Careerly account.</p>"
        f'<p><a href="{safe_link}">Reset your password</a></p>'
        "<p>The link works once and expires in 1 hour.</p>"
        "<p>If you didn't ask for this, you can ignore this email; your password won't change.</p>"
    )
    return send_email(to, "Reset your Careerly password", text, html_body)
