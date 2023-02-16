import asyncio
import logging

import asyncpg
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Initializing service")
    await init_db()
    logger.info("Service finished initializing")


@retry(
    stop=stop_after_attempt(5 * 60),
    wait=wait_fixed(1),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def init_db() -> None:
    try:
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_HOST,
        )
    except asyncpg.InvalidCatalogNameError as e:
        logger.error(e)
        await create_db()
        raise e

    try:
        await conn.fetch("SELECT 1")
        await conn.close()
    except Exception as e:
        logger.error(e)
        raise e


async def create_db() -> None:
    conn = await asyncpg.connect(
        database="template1",
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_HOST,
    )
    await conn.execute(
        f'CREATE DATABASE "{settings.POSTGRES_DB}" OWNER "{settings.POSTGRES_USER}"'
    )
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
