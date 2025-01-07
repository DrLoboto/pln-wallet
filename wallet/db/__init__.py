"""Database operations."""

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from wallet.config import get_settings

from . import models, services

__all__ = ["create_engine", "get_session", "init_db", "models", "services"]


def create_engine() -> AsyncEngine:
    """Create async DB engine instance."""
    settings = get_settings()
    return create_async_engine(settings.db, future=True, echo=settings.debug)


def get_session(engine: AsyncEngine) -> AsyncSession:
    """Get async DB session maker."""
    return async_sessionmaker(engine, class_=AsyncSession)()


async def init_db(*, reset: bool = False) -> None:
    """Apply DB schema."""
    engine = create_engine()
    async with engine.begin() as connection:
        if reset:
            await connection.run_sync(SQLModel.metadata.drop_all)
        await connection.run_sync(SQLModel.metadata.create_all)
    await engine.dispose()
