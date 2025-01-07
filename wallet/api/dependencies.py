"""FastAPI dependencines implementation and annotation definitions."""

import typing as t
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, Security
from sqlalchemy.ext.asyncio import AsyncEngine

from wallet.api.auth import Scope, get_user_id
from wallet.db import create_engine
from wallet.rates import create_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> t.AsyncIterator[None]:
    """Inject dependencies spanning app whole lifetime."""
    engine = create_engine()
    nbp_client = create_client()

    async with nbp_client:
        app.dependency_overrides = {
            create_engine: lambda: engine,
            create_client: lambda: nbp_client,
        }
        yield

    await engine.dispose()


EngineDependency = t.Annotated[AsyncEngine, Depends(create_engine)]
"""DB engine (FastAPI security dependency annotation)"""

NbpClientDependency = t.Annotated[httpx.AsyncClient, Depends(create_client)]
"""NBP Wen API client (FastAPI security dependency annotation)"""

UserIdReadScope = t.Annotated[
    int, Security(get_user_id, scopes=[Scope.READ, Scope.WRITE])
]
"""Current user ID with read allowed (FastAPI security dependency annotation)"""

UserIdWriteScope = t.Annotated[int, Security(get_user_id, scopes=[Scope.WRITE])]
"""Current user ID with write allowed (FastAPI security dependency annotation)"""
