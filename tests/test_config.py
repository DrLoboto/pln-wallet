import os
from unittest.mock import patch

from wallet.config import Settings, get_settings


def test_settings() -> None:
    settings = Settings(
        debug="False",
        title="An API",
        bind_host="localhost",
        bind_port="8000",
        db="DB connect",
        public_key="public key",
        private_key="private key",
        signing_algorithm="RSA",
        audience="wallet",
        nbp_url="an URL",
        nbp_timeout=100,
        nbp_connection_limit=5,
    )

    assert settings.debug is False
    assert settings.title == "An API"
    assert settings.bind_host == "localhost"
    assert settings.bind_port == 8000  # noqa: PLR2004
    assert isinstance(settings.bind_port, int)
    assert settings.db == "DB connect"
    assert settings.public_key == "public key"
    assert settings.private_key == "private key"
    assert settings.signing_algorithm == "RSA"
    assert settings.audience == "wallet"
    assert settings.nbp_url == "an URL"
    assert settings.nbp_timeout == 100  # noqa: PLR2004
    assert settings.nbp_connection_limit == 5  # noqa: PLR2004


@patch.dict(
    os.environ, wallet_private_key="private key", wallet_public_key="public key"
)
def test_get_settings(test_db_dsn: str) -> None:
    get_settings.cache_clear()

    settings = get_settings()
    expected = Settings(
        debug="Yes",
        title="Wallet API",
        bind_host="127.0.0.1",
        bind_port="8080",
        db=test_db_dsn,
        public_key="public key",
        private_key="private key",
        signing_algorithm="ES256",
        audience="wallet-api",
        nbp_url="https://api.nbp.pl/api",
        nbp_timeout=5,
        nbp_connection_limit=20,
    )

    assert settings == expected
    assert get_settings() is settings
