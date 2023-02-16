from typing import Any

import factory

from app.auth import models
from app.core.tests.factories import TortoiseModelFactory
from app.utils.security import hash_password


class UserFactory(TortoiseModelFactory[models.User]):
    email = factory.Faker("email")
    password = factory.Faker(
        "password",
        length=42,
        special_chars=True,
        digits=True,
        upper_case=True,
        lower_case=True,
    )
    full_name = factory.Faker("name")

    class Meta:
        model = models.User

    @classmethod
    async def _create(
        cls, model_class: type[models.User], *args: Any, **kwargs: Any
    ) -> models.User:
        kwargs["password"] = hash_password(kwargs["password"])
        return await super()._create(model_class, *args, **kwargs)
