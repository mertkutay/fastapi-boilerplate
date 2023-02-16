from ipaddress import IPv4Address, IPv6Address

from fastapi import Depends, Request
from geoip2.records import City, Continent, Country
from user_agents import parse
from user_agents.parsers import UserAgent

from app.utils.geolocation import GeoIP2

IPAddress = IPv4Address | IPv6Address


def get_user_agent(request: Request) -> UserAgent:
    return parse(request.headers["User-Agent"])


def get_ip_string(request: Request) -> str | None:
    x_forwarded_for = request.headers.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]

    return request.headers.get("REMOTE_ADDR")


def get_ip_address(ip_string: str = Depends(get_ip_string)) -> IPAddress:
    try:
        return IPv4Address(ip_string)
    except ValueError as e1:
        try:
            return IPv6Address(ip_string)
        except ValueError as e2:
            raise e2 from e1


def get_country(ip_address: IPAddress = Depends(get_ip_address)) -> Country:
    return GeoIP2().country(ip_address).country


def get_continent(ip_address: IPAddress = Depends(get_ip_address)) -> Continent:
    return GeoIP2().country(ip_address).continent


def get_city(ip_address: IPAddress = Depends(get_ip_address)) -> City:
    return GeoIP2().city(ip_address).city
