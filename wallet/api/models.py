"""Input/output API data models."""

import datetime as dt
import typing as t

from pydantic import BaseModel, PlainSerializer, computed_field

from wallet.db.models import Currency as DbCurrency
from wallet.rates import Rate

Float2Places = t.Annotated[
    float, PlainSerializer(lambda v: round(v, 4), when_used="json")
]
Float4Places = t.Annotated[
    float, PlainSerializer(lambda v: round(v, 4), when_used="json")
]


class Currency(BaseModel):
    """Current currency state in the wallet."""

    code: str
    """ISO 4217 code."""

    amount: Float2Places
    """Amount in a currency."""

    rate: Float4Places | None = None
    """Conversion to PLN rate if available."""

    date: dt.date | None = None
    """Exchange rate publication effective date."""

    @computed_field
    def pln_amount(self) -> float | None:
        """Amount in the PLN if available."""
        return round(self.amount * self.rate, 4) if self.rate is not None else None

    @classmethod
    def from_db(cls, db_currency: DbCurrency, rate: Rate | None) -> t.Self:
        """Create output model from DB one and rate."""
        result = cls(code=db_currency.code, amount=db_currency.amount)
        if rate:
            result.rate = rate.ask
            result.date = rate.date
        return result


class Wallet(BaseModel):
    """Current wallet state."""

    wallet: list[Currency]
    """Currencies states."""

    pln_total: Float4Places
    """Total wallet amount in PLN."""
