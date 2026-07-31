"""
Thin wrapper around Brevo's transactional email API (v3).
Docs: https://developers.brevo.com/reference/sendtransacemail
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BREVO_SEND_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"


class BrevoEmailError(Exception):
    pass


def send_otp_email(to_email: str, to_name: str, otp_code: str) -> None:
    """
    Sends the OTP to `to_email` via Brevo. Raises BrevoEmailError on failure
    so the caller can decide how to respond (e.g. return a 502 to the client).
    """
    payload = {
        "sender": {
            "name": settings.BREVO_SENDER_NAME,
            "email": settings.BREVO_SENDER_EMAIL,
        },
        "to": [{"email": to_email, "name": to_name or to_email}],
        "subject": "Your password change verification code",
        "htmlContent": (
            f"<p>Hi {to_name or ''},</p>"
            f"<p>Your verification code to change your password is:</p>"
            f"<h2 style='letter-spacing:4px'>{otp_code}</h2>"
            f"<p>This code expires in 10 minutes. If you didn't request this, "
            f"you can safely ignore this email.</p>"
        ),
    }

    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
    }

    try:
        response = requests.post(
            BREVO_SEND_EMAIL_URL, json=payload, headers=headers, timeout=10
        )
    except requests.RequestException as exc:
        logger.exception("Brevo request failed")
        raise BrevoEmailError(str(exc)) from exc

    if response.status_code not in (200, 201):
        logger.error("Brevo send failed: %s %s", response.status_code, response.text)
        raise BrevoEmailError(
            f"Brevo returned {response.status_code}: {response.text}"
        )