"""FastAPI dependency: extract and validate the current user from the
Authorization: Bearer <access_token> header."""

import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the JWT access token, look up the user, and return them.
    Raises 401 on any failure -- no DB hit if the token itself is invalid."""
    try:
        user_id = decode_access_token(credentials.credentials)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc) if str(exc) else "Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
