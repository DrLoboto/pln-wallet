import os
import typing as t

import httpx
import pytest
from pytest_httpx import HTTPXMock
from python_on_whales import DockerClient
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import SQLModel

from wallet.api.auth import Scope
from wallet.cli import create_token
from wallet.config import Settings, get_settings
from wallet.db import create_engine, get_session
from wallet.db.models import Currency
from wallet.main import create_app

TEST_HOST = "127.0.0.1"
TEST_USER = 123


@pytest.fixture(scope="session", autouse=True)
def start_docker() -> None:
    docker = DockerClient(compose_profiles=["testing"])
    docker.compose.up(detach=True)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Expicitly DO NOT mock requests to API under the test."""
    for item in items:
        if "https_mock" in getattr(item, "fixturenames", ()):
            item.add_marker(
                pytest.mark.httpx_mock(
                    should_mock=lambda request: request.url.host != TEST_HOST
                )
            )


@pytest.fixture(scope="session")
def test_postgres() -> str:
    return "postgresql+asyncpg://postgres:postgres@localhost:5433"


@pytest.fixture(scope="session")
def test_db() -> str:
    return "test_wallet"


@pytest.fixture(scope="session")
def test_db_dsn(test_postgres: str, test_db: str) -> str:
    return f"{test_postgres}/{test_db}"


@pytest.fixture(scope="session", autouse=True)
async def settings(test_db_dsn: str) -> Settings:
    os.environ["WALLET_BIND_HOST"] = TEST_HOST
    os.environ["WALLET_DB"] = test_db_dsn
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
async def engine() -> t.AsyncIterator[AsyncEngine]:
    engine = create_engine()
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.drop_all)
        await connection.run_sync(SQLModel.metadata.create_all)
    await engine.dispose()

    engine = create_engine()
    yield engine
    await engine.dispose()


@pytest.fixture
def user_id() -> int:
    return TEST_USER


@pytest.fixture
async def public_client(settings: Settings) -> t.AsyncIterator[httpx.AsyncClient]:
    base_url = f"http://{TEST_HOST}:{settings.bind_port}"
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url=base_url) as client:
        yield client


@pytest.fixture
async def read_client(
    public_client: httpx.AsyncClient, engine: AsyncEngine, nbp_mock: HTTPXMock
) -> httpx.AsyncClient:
    token = create_token(TEST_USER, (Scope.READ,), 1, "test")
    public_client.headers["Authorization"] = f"Bearer {token}"
    return public_client


@pytest.fixture
async def write_client(
    public_client: httpx.AsyncClient, engine: AsyncEngine, nbp_mock: HTTPXMock
) -> httpx.AsyncClient:
    token = create_token(TEST_USER, (Scope.WRITE,), 1, "test")
    public_client.headers["Authorization"] = f"Bearer {token}"
    return public_client


@pytest.fixture
def nbp_mock(httpx_mock: HTTPXMock, settings: Settings) -> HTTPXMock:
    rate_base_url = f"{settings.nbp_url}/exchangerates/rates/C"
    httpx_mock.add_response(
        method="GET",
        url=f"{rate_base_url}/USD/",
        json={
            "table": "C",
            "currency": "dolar amerykański",
            "code": "USD",
            "rates": [
                {
                    "no": "003/C/NBP/2025",
                    "effectiveDate": "2025-01-07",
                    "bid": 4.1028,
                    "ask": 4.1856,
                }
            ],
        },
        is_optional=True,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{rate_base_url}/AUD/",
        json={
            "table": "C",
            "currency": "dolar australijski",
            "code": "AUD",
            "rates": [
                {
                    "no": "002/C/NBP/2025",
                    "effectiveDate": "2025-01-03",
                    "bid": 2.5505,
                    "ask": 2.6021,
                }
            ],
        },
        is_optional=True,
    )
    httpx_mock.add_response(
        method="GET", url=f"{rate_base_url}/AED/", status_code=404, is_optional=True
    )
    return httpx_mock


@pytest.fixture
async def data(engine: AsyncEngine) -> None:
    async with get_session(engine) as session:
        session.add(Currency(user_id=TEST_USER, code="USD", amount=1234.56))
        session.add(Currency(user_id=TEST_USER, code="AUD", amount=15))
        session.add(Currency(user_id=TEST_USER, code="AED", amount=3000))
        await session.commit()
    await engine.dispose()
