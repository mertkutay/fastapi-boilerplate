import gettext as gettext_module
from contextvars import ContextVar

from app.core.config import settings

_lang: ContextVar[str] = ContextVar[str]("language", default=settings.DEFAULT_LOCALE)


def activate(lang: str) -> None:
    _lang.set(lang)


def get_language() -> str:
    return _lang.get()


def gettext(message: str) -> str:
    return gettext_module.translation(
        "messages", localedir="locale", languages=[get_language()]
    ).gettext(message)
