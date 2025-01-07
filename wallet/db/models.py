"""Database models."""

from decimal import Decimal

from sqlmodel import Field, Index, SQLModel


class Currency(SQLModel, table=True):
    """User currency amount."""

    id: int | None = Field(default=None, primary_key=True)
    """Primary key."""

    user_id: int
    """User ID."""

    code: str = Field(min_length=3, max_length=3)
    """ISO 4217 code."""

    amount: Decimal = Field(gt=0, decimal_places=2)
    """Money amount in a currency."""

    __tablename__ = "wallets"
    __table_args__ = (Index("unq_user_currency", "user_id", "code", unique=True),)
