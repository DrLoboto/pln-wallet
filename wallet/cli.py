"""Command line utilities."""

import asyncio
import datetime as dt

import click
import jwt
import uvicorn

from .config import get_settings
from .db import init_db


@click.command()
@click.option(
    "--reset", "-r", is_flag=True, default=False, help="drop existing database"
)
def prepare(*, reset: bool = False) -> None:
    """Create or update database."""
    asyncio.get_event_loop().run_until_complete(init_db(reset=reset))


@click.command()
def service() -> None:
    """Run web service."""
    settings = get_settings()

    if settings.debug:
        asyncio.get_event_loop().run_until_complete(init_db())

    uvicorn.run(
        "wallet.main:app",
        port=settings.bind_port,
        host=settings.bind_host,
        reload=settings.debug,
    )


@click.command()
@click.argument("user_id", type=int)
@click.argument("scope", nargs=-1)
@click.option("--ttl", type=int, default=5, help="token expiration time in minutes")
@click.option("--iss", type=str, default="manual", help="token issuer")
def token(user_id: int, scope: tuple[str], ttl: int, iss: str) -> None:
    """Create user login token for test purposes."""
    click.echo(create_token(user_id, scope, ttl, iss))


def create_token(user_id: int, scope: tuple[str], ttl: int, iss: str) -> str:
    """Create user login token."""
    settings = get_settings()
    if not settings.private_key:
        raise RuntimeError("private key for token signing is not configured")

    now = dt.datetime.now(dt.UTC)
    data = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + dt.timedelta(minutes=ttl),
        "iss": iss,
        "aud": settings.audience,
    }
    if scope:
        data["scopes"] = list(scope)

    return jwt.encode(
        data, key=settings.private_key, algorithm=settings.signing_algorithm
    )
