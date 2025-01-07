"""API user authentication and authorization utils."""

import typing as t
from enum import StrEnum

import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from jwt.exceptions import InvalidSubjectError, InvalidTokenError

from wallet.config import Settings, get_settings


class Scope(StrEnum):
    """Supported security scopes."""

    READ = "read"
    WRITE = "write"


class MissingScopeError(InvalidTokenError):
    """Auth token scope is not sufficient."""

    def __init__(self, security_scopes: SecurityScopes) -> None:
        self.security_scopes = security_scopes

    def __str__(self) -> str:
        return (
            'Token is missing any of the required scopes in "scopes" claim:'
            f" {self.security_scopes.scope_str}"
        )


def get_user_id(
    security_scopes: SecurityScopes,
    http_auth_credentials: t.Annotated[
        HTTPAuthorizationCredentials, Depends(HTTPBearer())
    ],
    settings: t.Annotated[Settings, Depends(get_settings)],
) -> int:
    """Validate auth token and get user ID from it."""
    claims = jwt.decode(
        http_auth_credentials.credentials,
        key=settings.public_key,
        algorithms=[settings.signing_algorithm],
        options={"require": ["exp", "iat", "aud", "sub"]},
        audience=settings.audience,
    )

    try:
        user_id = int(claims["sub"])
    except ValueError:
        raise InvalidSubjectError("Subject must be an integer string") from None

    if security_scopes.scopes:
        if scopes := claims.get("scopes"):
            for scope in security_scopes.scopes:
                if scope in scopes:
                    return user_id
        raise MissingScopeError(security_scopes)

    return user_id


async def http_exception_override_hander(
    request: Request, exc: HTTPException
) -> Response:
    """Transform general forbidden error to aunauthorized one."""
    if exc.status_code == status.HTTP_403_FORBIDDEN:
        exc.status_code = status.HTTP_401_UNAUTHORIZED
    return await http_exception_handler(request, exc)


async def token_exception_hander(
    request: Request,  # noqa: ARG001
    exc: InvalidTokenError,
) -> JSONResponse:
    """Handle token exceptions."""
    return JSONResponse({"detail": str(exc)}, status_code=status.HTTP_401_UNAUTHORIZED)


async def access_exception_hander(
    request: Request,  # noqa: ARG001
    exc: MissingScopeError,
) -> JSONResponse:
    """Handle token exceptions."""
    return JSONResponse({"detail": str(exc)}, status_code=status.HTTP_403_FORBIDDEN)


exception_handlers: dict[
    int | type[Exception],
    t.Callable[[Request, t.Any], t.Coroutine[t.Any, t.Any, Response]],
] = {
    MissingScopeError: access_exception_hander,
    InvalidTokenError: token_exception_hander,
    HTTPException: http_exception_override_hander,
}
