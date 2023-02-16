import asyncio
import logging

from tortoise import Tortoise

from app.auth.models import User
from app.core.config import TORTOISE_CONFIG, settings
from app.utils.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Initializing service")
    await Tortoise.init(config=TORTOISE_CONFIG)
    await Tortoise.generate_schemas()
    await create_first_superuser()
    logger.info("Service finished initializing")


async def create_first_superuser() -> None:
    await User.get_or_create(
        email=settings.FIRST_SUPERUSER_EMAIL,
        defaults={"password": hash_password(settings.FIRST_SUPERUSER_PASSWORD)},
    )


if __name__ == "__main__":
    asyncio.run(main())
