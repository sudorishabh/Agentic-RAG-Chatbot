from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

logger = logging.getLogger(__name__)

_ANONYMOUS_GROUPS: tuple[str, ...] = ("public",)

# auto_error=False so a missing Authorization header is handled here: allowed
# when auth is disabled, a 401 when it is enabled.
_bearer = HTTPBearer(auto_error=False)


class Principal:
    """The authenticated caller.

    Groups come from a verified token (or the anonymous default when auth is
    disabled), never from the request body. They do not scope retrieval — the
    corpus is public and every caller reads all of it — and are used only to
    widen access to the ops endpoints (see settings.ops_admin_group)."""

    __slots__ = ("user_groups",)

    def __init__(
        self, user_groups: tuple[str, ...] = _ANONYMOUS_GROUPS
    ) -> None:
        self.user_groups = user_groups

    @property
    def groups(self) -> list[str]:
        return list(self.user_groups)


def _principal_from_claims(claims: dict) -> Principal:
    settings = get_settings()
    raw_groups = claims.get(settings.jwt_groups_claim)
    if isinstance(raw_groups, str):
        groups = [g.strip() for g in raw_groups.split(",") if g.strip()]
    elif isinstance(raw_groups, (list, tuple)):
        groups = [str(g) for g in raw_groups if str(g).strip()]
    else:
        groups = []
    return Principal(tuple(groups) or _ANONYMOUS_GROUPS)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Principal:
    """FastAPI dependency yielding the caller's identity.

    Disabled auth returns the anonymous principal. Enabled auth requires a valid
    Bearer JWT and derives the identity from its claims. Either way the request
    body cannot influence the caller's groups.
    """
    settings = get_settings()
    if not settings.auth_enabled:
        return Principal()

    if credentials is None or not credentials.credentials:
        raise _unauthorized("Missing bearer token")
    if not settings.jwt_secret:
        logger.error("auth_enabled is true but jwt_secret is not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is misconfigured",
        )

    import jwt

    algorithms = [a.strip() for a in settings.jwt_algorithms.split(",") if a.strip()]
    options: dict = {"require": ["exp"]}
    decode_kwargs: dict = {"algorithms": algorithms, "options": options}
    if settings.jwt_audience:
        decode_kwargs["audience"] = settings.jwt_audience
    else:
        options["verify_aud"] = False
    if settings.jwt_issuer:
        decode_kwargs["issuer"] = settings.jwt_issuer

    try:
        claims = jwt.decode(credentials.credentials, settings.jwt_secret, **decode_kwargs)
    except jwt.PyJWTError:
        logger.info("Rejected request with invalid bearer token.", exc_info=True)
        raise _unauthorized("Invalid or expired token")

    return _principal_from_claims(claims)


def optional_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Principal:
    """Like require_principal, but a missing or invalid token degrades to the
    anonymous principal instead of a 401. For endpoints where identity only
    widens visibility (the ops metrics endpoints answer 404 to everyone else)
    and a 401 would advertise their existence."""
    try:
        return require_principal(credentials)
    except HTTPException:
        return Principal()
