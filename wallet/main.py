"""API entry point."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from wallet.api.dependencies import lifespan

from .api.auth import exception_handlers as auth_exception_handlers
from .api.routes import wallet_router
from .config import get_settings
from .rates import NotSupportedError


def create_app() -> FastAPI:
    """Create FastAPI application to serve requests."""
    settings = get_settings()
    app = FastAPI(
        debug=settings.debug,
        title=settings.title,
        exception_handlers=auth_exception_handlers
        | {NotSupportedError: not_supported_currency_exception_handler},
        lifespan=lifespan,
    )
    app.include_router(wallet_router)
    return app


async def not_supported_currency_exception_handler(
    request: Request,  # noqa: ARG001
    exc: NotSupportedError,
) -> JSONResponse:
    """Hande not supported currency error with 400 Bad Request response."""
    return JSONResponse({"detail": str(exc)}, status_code=status.HTTP_400_BAD_REQUEST)


app = create_app()
