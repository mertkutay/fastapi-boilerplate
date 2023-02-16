from pathlib import Path

import aiohttp


async def download_file(url: str, path: Path) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            res.raise_for_status()

            with open(path, "wb") as f:
                async for chunk in res.content.iter_chunked(1024):
                    f.write(chunk)
