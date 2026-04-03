"""JWT authentication dependencies."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import verify_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Dependency: decode JWT and return the authenticated User."""
    token_data = verify_token(token)
    user = await db.get(User, token_data.user_id)
    if not user:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthenticationError("User account is inactive")
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency: assert user is active."""
    if not current_user.is_active:
        raise AuthenticationError("Inactive user")
    return current_user


def require_roles(*roles: str):
    """Dependency factory — returns a dependency that enforces role membership."""
    async def _check_role(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role not in roles:
            raise AuthorizationError(
                f"This action requires one of: {', '.join(roles)}. Your role: {current_user.role}"
            )
        return current_user
    return _check_role
