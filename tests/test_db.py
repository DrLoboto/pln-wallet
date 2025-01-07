from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncEngine

from wallet.db import get_session
from wallet.db.models import Currency
from wallet.db.services import get_currency, update_currency


async def test_get_currency(engine: AsyncEngine) -> None:
    async with get_session(engine) as session:
        assert await get_currency(123, "USD", session) is None

        session.add(Currency(user_id=123, code="USD", amount=0.1))
        await session.commit()

        found = await get_currency(123, "USD", session)

    assert found
    assert found.id
    expected = Currency(id=found.id, user_id=123, code="USD", amount=0.1)
    assert found == expected


async def test_update_currency__success(engine: AsyncEngine) -> None:
    async with get_session(engine) as session:
        added = await update_currency(123, "USD", Decimal("15.5"), session)

        assert added.id

        expected = Currency(
            id=added.id, user_id=123, code="USD", amount=Decimal("15.5")
        )
        assert added == expected

        increased = await update_currency(123, "USD", Decimal("0.5"), session)

        expected.amount = Decimal("16.0")
        assert increased == expected

        decreased = await update_currency(123, "USD", Decimal("-15"), session)

        expected.amount = Decimal("1.0")
        assert decreased == expected


async def test_update_currency__error(engine: AsyncEngine) -> None:
    with pytest.raises(ValidationError):
        async with get_session(engine) as session:
            await update_currency(123, "USD", Decimal("-15.5"), session)
