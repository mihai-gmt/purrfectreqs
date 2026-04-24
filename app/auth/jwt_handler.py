"""
JWT token creation for the auth module.

Uses PyJWT with HS256 to generate access tokens.
Secret key and expiry are loaded from app/core/config.py settings.

Why PyJWT over python-jose?
  PyJWT is a smaller, focused library that does exactly what we need:
  encode/decode JWT with HMAC. python-jose adds JWE/JWK support we
  don't use and has a larger dependency footprint.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from app.core.config import settings


def create_access_token(user_id: int, role: str) -> str:
    """
    Create a signed JWT access token.

    Claims:
      - sub: user ID as string (JWT standard: subject is always a string)
      - role: user's RBAC role
      - exp: expiration time (UTC)
      - iat: issued-at time (UTC)
      - jti: unique token ID (UUID hex, for future revocation support)

    Args:
        user_id: The authenticated user's database ID.
        role: The user's role string (e.g. "super_user", "admin").

    Returns:
        An encoded JWT string.
    """
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        "iat": now,
        "jti": uuid4().hex,
    }
    return jwt.encode(  # type: ignore[no-any-return]  # PyJWT stubs return Any; actual return is str
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
