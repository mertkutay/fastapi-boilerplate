import tarfile
from pathlib import Path
from urllib.parse import urlencode

import geoip2.database
from geoip2.models import City, Country
from geoip2.types import IPAddress

from app.core.config import settings
from app.utils.download import download_file


class Singleton:
    def __new__(cls) -> "Singleton":
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
        return cls.instance


class GeoIP2Exception(Exception):
    pass


class GeoIP2(Singleton):
    download_url = "https://download.maxmind.com/app/geoip_download"

    _city: geoip2.database.Reader | None = None
    _country: geoip2.database.Reader | None = None

    def __init__(self) -> None:
        city_db = self.db_path("City")
        if city_db.is_file():
            self._city = geoip2.database.Reader(str(city_db))

        country_db = self.db_path("Country")
        if country_db.is_file():
            self._country = geoip2.database.Reader(str(country_db))

        if not self._country and not self._city:
            raise GeoIP2Exception("Could not load geoip databases")

    def __del__(self) -> None:
        if self._city:
            self._city.close()

        if self._country:
            self._country.close()

    @staticmethod
    def db_path(edition: str) -> Path:
        return settings.GEOIP_PATH / f"GeoLite2-{edition.title()}.mmdb"

    @classmethod
    async def download(cls, edition: str, force: bool = False) -> None:
        edition = edition.title()

        settings.GEOIP_PATH.mkdir(exist_ok=True, parents=True)

        if cls.db_path(edition).exists() and not force:
            return

        query = {
            "edition_id": f"GeoLite2-{edition}",
            "license_key": settings.GEOIP_LICENSE,
            "suffix": "tar.gz",
        }
        file_name = f"{query['edition_id']}.{query['suffix']}"
        file_path = settings.GEOIP_PATH / file_name
        await download_file(f"{cls.download_url}?{urlencode(query)}", file_path)

        with tarfile.open(file_path, "r:gz") as tar:
            mmdb_path = next(
                filter(lambda name: name.endswith(".mmdb"), tar.getnames())
            )
            reader = tar.extractfile(mmdb_path)
            if reader:
                cls.db_path(edition).write_bytes(reader.read())

    def city(self, query: IPAddress) -> City:
        if not self._city:
            raise GeoIP2Exception("City database is not loaded")

        return self._city.city(query)

    def country(self, query: IPAddress) -> Country:
        if not self._country:
            raise GeoIP2Exception("Country database is not loaded")

        return self._country.country(query)

    def coords(self, query: IPAddress) -> tuple[float | None, float | None]:
        city = self.city(query)
        return city.location.latitude, city.location.longitude
