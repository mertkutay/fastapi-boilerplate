import secrets
import string

from slugify import slugify
from tortoise import models


def key_generator(length: int = 8) -> str:
    key = "".join(
        secrets.choice(string.ascii_lowercase + string.digits) for _ in range(length)
    )
    return key


def unique_slug_generator(
    model: type[models.Model], value: str, *, max_length: int = 50, suffix: str = ""
) -> str:
    slug = slugify(value)[:50]
    if suffix:
        cut = 49 - len(suffix)
        slug = slug[:cut] + "-" + suffix

    qs_exists = model.exists(slug=slug)
    if qs_exists:
        return unique_slug_generator(
            model, value, max_length=max_length, suffix=key_generator(4)
        )

    return slug
