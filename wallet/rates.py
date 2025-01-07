"""NBP Web API interaction services."""

import datetime as dt
import logging
from dataclasses import dataclass

import httpx

from .config import get_settings

logger = logging.getLogger("uvicorn.error")


@dataclass(kw_only=True)
class Rate:
    """Exchange rate info."""

    code: str
    ask: float
    date: dt.date


class NotSupportedError(ValueError):
    """Not supported currency."""

    def __init__(self, code: str) -> None:
        super().__init__(f'Not supported currency "{code}"')


def create_client() -> httpx.AsyncClient:
    """Get NBP Web API requests client."""
    settings = get_settings()
    limits = httpx.Limits(max_connections=settings.nbp_connection_limit)
    return httpx.AsyncClient(
        base_url=settings.nbp_url,
        headers={"Accept": "application/json"},
        limits=limits,
        timeout=settings.nbp_timeout,
    )


async def get_rate(client: httpx.AsyncClient, currency: str) -> Rate | None:
    """Get currency exchange rate."""
    result = await client.get(f"/exchangerates/rates/C/{currency}/")

    if result.status_code == httpx.codes.NOT_FOUND:
        raise NotSupportedError(currency)

    if not result.is_success:
        logger.error(
            "NBP API request %s resulted in %s %s: %s",
            result.url,
            result.status_code,
            result.reason_phrase,
            result.content,
        )
        return None

    try:
        data = result.json()
    except Exception:  # noqa: BLE001
        logger.error(  # noqa: TRY400
            "NBP API request %s resulted in %s %s: %s",
            result.url,
            result.status_code,
            result.reason_phrase,
            result.content,
        )
        return None

    return Rate(
        code=data["code"],
        ask=data["rates"][0]["ask"],
        date=dt.date.fromisoformat(data["rates"][0]["effectiveDate"]),
    )
