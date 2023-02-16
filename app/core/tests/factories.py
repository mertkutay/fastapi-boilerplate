from typing import Any, Generic

from app.core.tests.async_factory import TM, AsyncFactory


class TortoiseModelFactory(AsyncFactory, Generic[TM]):
    @classmethod
    async def _create(cls, model_class: type[TM], *args: Any, **kwargs: Any) -> TM:
        return await model_class.create(**kwargs)
