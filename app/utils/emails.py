import logging
from typing import Any

import emails
from emails.template import JinjaTemplate

from app.core.config import Environment, settings


class EmailSender:
    options = {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "user": settings.SMTP_USER,
        "password": settings.SMTP_PASSWORD,
        "tls": settings.SMTP_TLS,
    }

    @classmethod
    def send_html_email(
        cls,
        recipients: list[str],
        subject: str,
        template_name: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        with open(f"templates/email/build/{template_name}.html") as f:
            template = f.read()

        cls.send_email(recipients, subject, "", template, context)

    @classmethod
    def send_email(
        cls,
        recipients: list[str],
        subject_template: str,
        text_template: str,
        html_template: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        message = emails.Message(
            subject=JinjaTemplate(f"[{settings.PROJECT_NAME}] {subject_template}"),
            text=JinjaTemplate(text_template),
            html=JinjaTemplate(html_template),
            mail_from=settings.EMAIL_FROM,
        )
        if settings.ENVIRONMENT > Environment.test:
            res = message.send(to=recipients, render=context, smtp=cls.options)
            res.raise_if_needed()
        elif settings.ENVIRONMENT == Environment.test:
            pass
        else:
            logging.info(message.html_body)
