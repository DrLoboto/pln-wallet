"""Application configuration setup."""

import typing as t
from functools import lru_cache

from pydantic import BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_bool(value: bool | str) -> bool:
    """Parse boolean value from string."""
    return value.lower() in {"true", "yes", "1"} if isinstance(value, str) else value


class Settings(BaseSettings):
    """
    Application settings.

    Missing values and overrides could be provided as environment variables with field
    names prefixed with WALLET_. It is also possible to put them into .env file in the
    current working directory which may contain export clauses if needed. In case both
    environment variable and a key in an .env file is provided the environment variable
    wins. Names are case-insesitive.
    """

    debug: t.Annotated[bool, BeforeValidator(parse_bool)] = False
    """Start service in a debug mode."""

    title: str = "Wallet API"
    """Title for OpenAPI documentation."""

    bind_host: str = "127.0.0.1"
    """Host to bind service to."""

    bind_port: int = 8080
    """Port to bind service to."""

    db: str
    """Database connection string."""

    public_key: str
    """Auth tokens signature public key."""

    private_key: str | None = None
    """Auth tokens signature secret key. Dev only."""

    signing_algorithm: str
    """Auth tokens signing algorithm."""

    audience: str = "wallet-api"
    """Auth tokens expected audience."""

    nbp_url: str = "https://api.nbp.pl/api"
    """NBP Web API URL up to API path portion."""

    nbp_timeout: int = 5
    """NBP Web API request timeout in seconds."""

    nbp_connection_limit: int = 20
    """NBP Web API maximal allowed concurrent connections number."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="wallet_", extra="forbid"
    )


@lru_cache
def get_settings() -> Settings:
    """Application settings getter."""
    return Settings()
