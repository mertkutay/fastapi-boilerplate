import math

from fastapi import Depends, HTTPException, Request, status
from redis.commands.core import AsyncScript

from app.core.cache import Cache
from app.core.deps import get_ip_string


class RateLimiter:
    script_str = """local key = KEYS[1]
local limit = tonumber(ARGV[1])
local expire_time = ARGV[2]
local current = tonumber(redis.call('get', key) or "0")
if current > 0 then
  if current + 1 > limit then
    return redis.call("PTTL",key)
  else
    redis.call("INCR", key)
    return 0
  end
else
  redis.call("SET", key, 1,"px",expire_time)
  return 0
end"""

    script: AsyncScript = Cache.register_script(script_str)

    def __init__(
        self,
        times: int = 1,
        milliseconds: int = 0,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
    ) -> None:
        self.times = times
        self.milliseconds = (
            milliseconds + 1000 * seconds + 60000 * minutes + 3600000 * hours
        )

    async def _check(self, key: str) -> int:
        return await self.script([key], [str(self.times), str(self.milliseconds)])

    async def __call__(
        self, request: Request, ip_string: str = Depends(get_ip_string)
    ) -> None:
        key = f"limiter:{ip_string}:{request.method}:{request.url.path}"
        pexpire = await self._check(key)
        if pexpire != 0:
            expire = math.ceil(pexpire / 1000)
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Too Many Requests",
                headers={"Retry-After": str(expire)},
            )
