import httpx
import pytest


@pytest.mark.usefixtures("data")
async def test_read_currency__found(read_client: httpx.AsyncClient) -> None:
    result = await read_client.get("/wallet/USD")
    assert result.status_code == httpx.codes.OK, result.content
    assert result.json() == {
        "amount": 1234.56,
        "code": "USD",
        "date": "2025-01-07",
        "pln_amount": 5167.3743,
        "rate": 4.1856,
    }


async def test_read_currency__not_found(read_client: httpx.AsyncClient) -> None:
    result = await read_client.get("/wallet/USD")
    assert result.status_code == httpx.codes.NOT_FOUND, result.content
    assert result.json() == {"detail": "There is no USD in the wallet."}


async def test_read_currency__not_authorized(public_client: httpx.AsyncClient) -> None:
    result = await public_client.get("/wallet/USD")
    assert result.status_code == httpx.codes.UNAUTHORIZED, result.content
    assert result.json() == {"detail": "Not authenticated"}


async def test_read_currency__invalid_token(public_client: httpx.AsyncClient) -> None:
    public_client.headers["Authorization"] = "Bearer not-a-valid-token"

    result = await public_client.get("/wallet/USD")
    assert result.status_code == httpx.codes.UNAUTHORIZED, result.content
    assert result.json() == {"detail": "Not enough segments"}


async def test_add_amount__not_supported(write_client: httpx.AsyncClient) -> None:
    result = await write_client.post("/wallet/AED/add/15")
    assert result.status_code == httpx.codes.BAD_REQUEST, result.content
    assert result.json() == {"detail": 'Not supported currency "AED"'}


async def test_delete_currency__scope_error(read_client: httpx.AsyncClient) -> None:
    result = await read_client.delete("/wallet/USD")
    assert result.status_code == httpx.codes.FORBIDDEN, result.content
    assert result.json() == {
        "detail": 'Token is missing any of the required scopes in "scopes" claim: write'
    }


@pytest.mark.usefixtures("data")
async def test_read_wallet(read_client: httpx.AsyncClient, user_id: str) -> None:
    result = await read_client.get("/wallet/")
    assert result.status_code == httpx.codes.OK, result.content
    assert result.json() == {
        "wallet": [
            {
                "amount": 1234.56,
                "code": "USD",
                "date": "2025-01-07",
                "pln_amount": 5167.3743,
                "rate": 4.1856,
            },
            {
                "amount": 15,
                "code": "AUD",
                "date": "2025-01-03",
                "pln_amount": 39.0315,
                "rate": 2.6021,
            },
            {
                "amount": 3000,
                "code": "AED",
                "date": None,
                "pln_amount": None,
                "rate": None,
            },
        ],
        "pln_total": 5206.4058,
    }
