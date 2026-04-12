"""JWT authentication and password hashing utilities."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import get_settings

settings = get_settings()


class TokenData(BaseModel):
    user_id: UUID
    email: str
    role: str


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token.

    Args:
        data: Payload dict. Must include 'sub' (email), 'user_id', 'role'.
        expires_delta: Custom expiry. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> TokenData:
    """Decode and validate a JWT token.

    Args:
        token: Raw JWT string from Authorization header.

    Returns:
        Parsed TokenData.

    Raises:
        AuthenticationError: If token is invalid, expired, or malformed.
    """
    from app.core.exceptions import AuthenticationError

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: Optional[str] = payload.get("sub")
        user_id: Optional[str] = payload.get("user_id")
        role: Optional[str] = payload.get("role")
        if email is None or user_id is None or role is None:
            raise AuthenticationError("Could not validate credentials")
        return TokenData(user_id=UUID(user_id), email=email, role=role)
    except JWTError as exc:
        raise AuthenticationError("Could not validate credentials") from exc
    except (ValueError, KeyError) as exc:
        raise AuthenticationError("Could not validate credentials") from exc


def get_password_hash(password: str) -> str:
    """Hash a plaintext password with bcrypt (12 rounds)."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
