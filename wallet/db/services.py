"""DB access functions."""

from decimal import Decimal

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import Currency


async def get_wallet(user_id: int, session: AsyncSession) -> list[Currency]:
    """Retrieve wallet data."""
    results = await session.exec(select(Currency).where(Currency.user_id == user_id))
    return results.all()  # type: ignore[return-value]  # it is 100% a list


async def get_currency(
    user_id: int, currency: str, session: AsyncSession
) -> Currency | None:
    """Retrieve single currency from wallet."""
    statement = (
        select(Currency)
        .where(Currency.user_id == user_id)
        .where(Currency.code == currency)
    )
    results = await session.exec(statement)
    return results.first()


async def update_currency(
    user_id: int, currency: str, add_amount: Decimal, session: AsyncSession
) -> Currency:
    """
    Update single currency in a wallet.

    Add amount could be positive, in this case currency will be added to the wallet if
    not exists there already. In other case this currency must exist already in the
    wallet.
    """
    record = await get_currency(user_id=user_id, currency=currency, session=session)

    if not record:
        record = Currency(user_id=user_id, code=currency, amount=add_amount)
    else:
        record.amount += add_amount
    Currency.model_validate(record)

    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def delete_currency(user_id: int, currency: str, session: AsyncSession) -> bool:
    """Remove currency from a wallet returning operation success."""
    record = await get_currency(user_id=user_id, currency=currency, session=session)
    if record:
        await session.delete(record)
        await session.commit()
        return True
    return False
