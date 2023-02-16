import inspect
from typing import Any, Generic, TypeVar

import factory
from factory import enums
from factory.base import Factory, FactoryOptions
from factory.builder import BuildStep, StepBuilder, parse_declarations
from tortoise import models

TM = TypeVar("TM", bound=models.Model)


class AsyncFactoryOptions(FactoryOptions, Generic[TM]):
    factory: "AsyncFactory"

    async def instantiate(self, step: BuildStep, args: list, kwargs: dict) -> TM:
        model = self.get_model_class()

        for key, value in kwargs.items():
            if inspect.isawaitable(value):
                kwargs[key] = await value

        if step.builder.strategy == enums.BUILD_STRATEGY:
            return self.factory._build(model, *args, **kwargs)
        elif step.builder.strategy == enums.CREATE_STRATEGY:
            return await self.factory._create(model, *args, **kwargs)
        else:
            raise ValueError("invalid strategy")

    async def use_postgeneration_results(
        self, step: BuildStep, instance: TM, results: dict[str, Any]
    ) -> None:
        if self.factory:
            await self.factory._after_postgeneration(
                instance,
                create=step.builder.strategy == enums.CREATE_STRATEGY,
                results=results,
            )


class AsyncFactory(Factory, Generic[TM]):
    _options_class = AsyncFactoryOptions

    class Meta:
        abstract = True

    @classmethod
    async def build(cls, **kwargs: Any) -> TM:
        return await cls._generate(enums.BUILD_STRATEGY, kwargs)

    @classmethod
    async def create(cls, **kwargs: Any) -> TM:
        return await cls._generate(enums.CREATE_STRATEGY, kwargs)

    @classmethod
    async def create_batch(cls, size: int, **kwargs: Any) -> list[TM]:
        return [await cls.create(**kwargs) for _ in range(size)]

    @classmethod
    async def _generate(cls, strategy: str, params: dict[str, Any]) -> TM:
        if cls._meta.abstract:
            raise factory.errors.FactoryError(
                "Cannot generate instances of abstract factory %(f)s; "
                f"Ensure {cls.__name__}.Meta.model is set and %(f)s.Meta.abstract "
                "is either not set or False."
            )

        step = AsyncStepBuilder[TM](cls._meta, params, strategy)
        return await step.build()

    @classmethod
    async def _after_postgeneration(
        cls, instance: TM, create: bool, results: dict[str, Any] | None = None
    ) -> None:
        if create and results:
            await instance.save()


class AsyncStepBuilder(StepBuilder, Generic[TM]):
    factory_meta: AsyncFactoryOptions

    async def build(
        self, parent_step: BuildStep | None = None, force_sequence: int | None = None
    ) -> TM:
        pre, post = parse_declarations(
            self.extras,
            base_pre=self.factory_meta.pre_declarations,
            base_post=self.factory_meta.post_declarations,
        )

        if force_sequence is not None:
            sequence = force_sequence
        elif self.force_init_sequence is not None:
            sequence = self.force_init_sequence
        else:
            sequence = self.factory_meta.next_sequence()

        step = BuildStep(builder=self, sequence=sequence, parent_step=parent_step)
        step.resolve(pre)

        args, kwargs = self.factory_meta.prepare_arguments(step.attributes)

        instance = await self.factory_meta.instantiate(
            step=step, args=args, kwargs=kwargs
        )

        postgen_results = {}
        for declaration_name in post.sorted():
            declaration = post[declaration_name]
            declaration_result = declaration.declaration.evaluate_post(
                instance=instance,
                step=step,
                overrides=declaration.context,
            )
            if inspect.isawaitable(declaration_result):
                declaration_result = await declaration_result
            postgen_results[declaration_name] = declaration_result

        await self.factory_meta.use_postgeneration_results(
            instance=instance,
            step=step,
            results=postgen_results,
        )
        return instance
