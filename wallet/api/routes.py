"""API endpoints."""

import asyncio
import typing as t
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Path, status
from pydantic import AfterValidator
from sqlalchemy.ext.asyncio import AsyncEngine

from wallet.db import get_session
from wallet.db import services as db_services
from wallet.db.models import Currency as DbCurrency
from wallet.rates import NotSupportedError, Rate, get_rate

from . import dependencies, models

wallet_router = APIRouter(prefix="/wallet", tags=["User wallet operations"])


@wallet_router.get("/")
async def read_wallet(
    user_id: dependencies.UserIdReadScope,
    engine: dependencies.EngineDependency,
    nbp_client: dependencies.NbpClientDependency,
) -> models.Wallet:
    """Get current wallet composition."""
    async with get_session(engine) as session:
        db_wallet = await db_services.get_wallet(user_id, session)

    rates = {
        rate.code: rate
        for rate in await asyncio.gather(
            *(get_rate(nbp_client, currency.code) for currency in db_wallet),
            return_exceptions=True,
        )
        if isinstance(rate, Rate)
    }

    output_wallet = [
        models.Currency.from_db(db_currency, rates.get(db_currency.code))
        for db_currency in db_wallet
    ]

    return models.Wallet(
        wallet=output_wallet,
        pln_total=sum(item.pln_amount for item in output_wallet if item.rate),
    )


def to_upper(value: str) -> str:
    """Convert string to uppercase."""
    return value.upper()


CurrencyAnnotation = t.Annotated[
    str,
    Path(title="ISO 4217 3-letter currency code", min_length=3, max_length=3),
    AfterValidator(to_upper),
]


@wallet_router.get("/{currency}")
async def read_currency(
    currency: CurrencyAnnotation,
    user_id: dependencies.UserIdReadScope,
    engine: dependencies.EngineDependency,
    nbp_client: dependencies.NbpClientDependency,
) -> models.Currency:
    """Show currency state in the wallet."""
    async with get_session(engine) as session:
        db_currency = await db_services.get_currency(user_id, currency, session)

    if not db_currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"There is no {currency} in the wallet.",
        )

    rate: Rate | None
    try:
        rate = await get_rate(nbp_client, currency)
    except NotSupportedError:
        rate = None

    return models.Currency.from_db(db_currency, rate)


@wallet_router.post("/{currency}/add/{amount}")
async def add_amount(
    currency: CurrencyAnnotation,
    amount: t.Annotated[Decimal, Path(title="Amount to add", gt=0, decimal_places=2)],
    user_id: dependencies.UserIdWriteScope,
    engine: dependencies.EngineDependency,
    nbp_client: dependencies.NbpClientDependency,
) -> models.Currency:
    """Add a specified amount of a currency to the wallet."""
    rate = await get_rate(nbp_client, currency)

    db_currency = await update_amount(
        currency=currency, amount=amount, user_id=user_id, engine=engine
    )

    return models.Currency.from_db(db_currency, rate)


@wallet_router.post("/{currency}/sub/{amount}")
async def substract_amount(
    currency: CurrencyAnnotation,
    amount: t.Annotated[
        Decimal, Path(title="Amount to subtract", gt=0, decimal_places=2)
    ],
    user_id: dependencies.UserIdWriteScope,
    engine: dependencies.EngineDependency,
    nbp_client: dependencies.NbpClientDependency,
) -> models.Currency:
    """Substract a specified amount of a currency from the wallet."""
    rate = await get_rate(nbp_client, currency)

    try:
        db_currency = await update_amount(
            currency=currency, amount=-amount, user_id=user_id, engine=engine
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot decrease amount to zero or below.",
        ) from None

    return models.Currency.from_db(db_currency, rate)


@wallet_router.delete("/{currency}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_currency(
    currency: CurrencyAnnotation,
    user_id: dependencies.UserIdWriteScope,
    engine: dependencies.EngineDependency,
) -> None:
    """Remove currency from the wallet."""
    async with get_session(engine) as session:
        success = await db_services.delete_currency(user_id, currency, session)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"There is no {currency} in the wallet.",
        )


async def update_amount(
    currency: str, amount: Decimal, user_id: int, engine: AsyncEngine
) -> DbCurrency:
    """Update currency amount in the wallet."""
    async with get_session(engine) as session:
        return await db_services.update_currency(
            user_id=user_id, currency=currency, add_amount=amount, session=session
        )
