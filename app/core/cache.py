import asyncio
import inspect
import pickle
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, ParamSpec, TypeAlias, TypeVar, cast
from urllib.parse import urlencode

from fastapi import Request, Response
from fastapi.concurrency import run_in_threadpool
from redis import asyncio as aioredis
from redis.commands.core import AsyncScript

from app.core import translation
from app.core.config import settings


class Cache:
    client = aioredis.from_url(settings.CACHE_URI)

    @classmethod
    async def get(cls, key: str, default: Any = None) -> Any:
        ret = await cls.client.get(key)
        if ret is None:
            return default
        return pickle.loads(ret)

    @classmethod
    async def get_with_ttl(cls, key: str, default: Any = None) -> tuple[Any, int]:
        async with cls.client.pipeline(transaction=True) as pipe:
            ret, ttl = await pipe.get(key).ttl(key).execute()
            if not ret:
                return default, ttl
            return pickle.loads(ret), ttl

    @classmethod
    async def set(cls, key: str, value: Any, timeout: int = 3 * 60) -> None:
        await cls.client.set(key, pickle.dumps(value), ex=timeout)

    @classmethod
    async def delete(cls, *keys: str) -> None:
        await asyncio.gather(*[cls.client.delete(key) for key in keys])

    @classmethod
    def register_script(cls, script: str) -> AsyncScript:
        return cls.client.register_script(script)


class CacheInvalidator:
    def __init__(self, main_key: str) -> None:
        self.main_key = main_key.lower()

    @classmethod
    async def invalidate(cls, main_key: str) -> None:
        obj = cls(main_key)
        keys = await obj.get_flush_list()
        await Cache.delete(*keys)
        await obj.set_flush_list(set())

    async def get_flush_list(self) -> set:
        return await Cache.get(self._flush_key, set())

    async def set_flush_list(self, flush_list: set) -> None:
        await Cache.set(self._flush_key, flush_list, timeout=24 * 60 * 60)

    async def add_to_flush_list(self, new_key: str) -> None:
        flush_list = await self.get_flush_list()
        flush_list.add(new_key)
        await self.set_flush_list(flush_list)

    @property
    def _flush_key(self) -> str:
        return f"{self.main_key}_flushlist"


class CacheHandler:
    def __init__(self, main_key: str) -> None:
        self.main_key = main_key.lower()

    @property
    def invalidator(self) -> CacheInvalidator:
        return CacheInvalidator(self.main_key)

    async def get(self, sub_key: str, default: Any = None) -> Any:
        return await Cache.get(self._cache_key(sub_key), default)

    async def get_with_ttl(self, sub_key: str, default: Any = None) -> tuple[Any, int]:
        return await Cache.get_with_ttl(self._cache_key(sub_key), default)

    async def set(self, sub_key: str, result: Any, timeout: int = 300) -> None:
        cache_key = self._cache_key(sub_key)
        await Cache.set(cache_key, result, timeout)
        await self.invalidator.add_to_flush_list(cache_key)

    def _cache_key(self, sub_key: str) -> str:
        return f"{self.main_key}_{sub_key}"


P = ParamSpec("P")
R = TypeVar("R")
Result: TypeAlias = R | Awaitable[R] | Response
Route: TypeAlias = Callable[P, Result]


def check_request_response(func: Route) -> tuple[bool, bool]:
    signature = inspect.signature(func)

    request_exists = False
    response_exists = False
    for param in signature.parameters.values():
        if param.annotation is Request:
            request_exists = True
        if param.annotation is Response:
            response_exists = True

    parameters = list(signature.parameters.values())
    if not request_exists:
        parameters.append(
            inspect.Parameter(
                name="request",
                annotation=Request,
                kind=inspect.Parameter.KEYWORD_ONLY,
            ),
        )
    if not response_exists:
        parameters.append(
            inspect.Parameter(
                name="response",
                annotation=Response,
                kind=inspect.Parameter.KEYWORD_ONLY,
            ),
        )
    if parameters:
        signature = signature.replace(parameters=parameters)

    func.__signature__ = signature  # type: ignore

    return request_exists, response_exists


class cache_route:
    def __init__(self, expire: int = 5 * 60) -> None:
        self.expire = expire

    def __call__(self, func: Route) -> Route:
        request_exists, response_exists = check_request_response(func)

        @wraps(func)  # type: ignore
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result:
            request: Request = cast(Request, kwargs["request"])
            response: Response = cast(Response, kwargs["response"])

            if not request_exists:
                kwargs.pop("request")
            if not response_exists:
                kwargs.pop("response")

            async def run_function() -> Result:
                if inspect.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return await run_in_threadpool(func, *args, **kwargs)

            if request.method != "GET" or request.headers.get("Cache-Control") in (
                "no-store",
                "no-cache",
            ):
                return await run_function()

            main_key = request.url.path.lower()
            language = translation.get_language()
            querystring = urlencode(sorted(request.query_params.items()))
            sub_key = f"{language}_{querystring}".lower()

            cache = CacheHandler(main_key)
            ret, ttl = await cache.get_with_ttl(sub_key)

            if ret is not None:
                response.headers["Cache-Control"] = f"max-age={ttl}"
                etag = f"W/{hash(pickle.dumps(ret))}"
                if request.headers.get("if-none-match") == etag:
                    response.status_code = 304
                    return response

                response.headers["ETag"] = etag
                return ret

            ret = await run_function()
            await cache.set(sub_key, ret, timeout=self.expire)

            response.headers["Cache-Control"] = f"max-age={self.expire}"
            response.headers["ETag"] = f"W/{hash(pickle.dumps(ret))}"

            return ret

        return cast(Route, wrapper)
