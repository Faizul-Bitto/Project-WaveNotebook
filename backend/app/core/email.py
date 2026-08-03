from pathlib import Path

import httpx
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings
from app.core.logger import logger

# Email template directory
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"

# Jinja2 template environment
template_environment = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
)


def render_email_template(
    template_name: str,
    **context,
) -> str:
    """
    Render an HTML email template.
    """

    template = template_environment.get_template(template_name)
    return template.render(**context)


def verify_email_connection() -> bool:
    """
    Verify Brevo API connectivity.
    """

    logger.info("📧 Verifying Brevo API connection...")

    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
    }

    try:
        response = httpx.get(
            "https://api.brevo.com/v3/account",
            headers=headers,
            timeout=10,
        )

        response.raise_for_status()

        logger.info("✅ Brevo API connected successfully.")
        return True

    except httpx.HTTPError as exc:
        logger.exception("❌ Failed to connect to Brevo API.")
        raise RuntimeError("Unable to connect to Brevo API.") from exc


def send_email(
    recipient_email: str,
    subject: str,
    body: str,
    html_body: str | None = None,
) -> bool:
    """
    Send an email using the Brevo API.
    """

    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            "name": settings.EMAIL_FROM_NAME,
            "email": settings.EMAIL_FROM,
        },
        "to": [
            {
                "email": recipient_email,
            }
        ],
        "subject": subject,
        "textContent": body,
    }

    if html_body is not None:
        payload["htmlContent"] = html_body

    try:
        response = httpx.post(
            "https://api.brevo.com/v3/smtp/email",
            headers=headers,
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

        logger.info(
            "📨 Email sent successfully to %s",
            recipient_email,
        )

        return True

    except httpx.HTTPError as exc:
        logger.exception(
            "❌ Failed to send email to %s",
            recipient_email,
        )
        raise RuntimeError("Failed to send email.") from exc
