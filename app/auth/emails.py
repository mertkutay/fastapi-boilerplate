from gettext import gettext as _

from app.auth import models
from app.core.config import settings
from app.utils import security
from app.utils.emails import EmailSender


def send_password_reset_email(user: models.User) -> None:
    token = security.create_password_reset_token(user.id)
    url = settings.CLIENT_URL + f"/reset-password?token={token}"
    subject = _("Password Reset")
    context = {
        "lang": "en",
        "subject": subject,
        "title": subject,
        "heading": "",
        "button": _("Reset My Password"),
        "url": url,
    }

    EmailSender.send_html_email([user.email], subject, "password-reset", context)


def send_verification_email(user: models.User) -> None:
    token = security.create_email_verification_token(user.email)
    url = settings.CLIENT_URL + f"/verify-email?token={token}"
    subject = _("Email Verification")
    context = {
        "lang": "en",
        "subject": subject,
        "title": subject,
        "heading": "",
        "button": _("Verify My Email"),
        "url": url,
    }

    EmailSender.send_html_email([user.email], subject, "email-verification", context)
