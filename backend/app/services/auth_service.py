"""Auth service -- signup, login, refresh-token rotation, logout.
Implements the flow from Section 3 and 8.5 of the design document."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    hash_refresh_token,
    generate_refresh_token,
)
from app.models.user import User
from app.models.refresh_token import RefreshToken


async def signup(
    db: AsyncSession,
    *,
    name: str,
    email: str,
    password: str,
) -> tuple[User, str, str]:
    """Create a new user, return (user, access_token, raw_refresh_token)."""
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = User(name=name, email=email, password_hash=hash_password(password))
    db.add(user)
    await db.flush()

    access_token = create_access_token(user.id)
    raw_refresh = await _issue_refresh_token(db, user.id)
    await db.commit()
    await db.refresh(user)

    return user, access_token, raw_refresh


async def login(
    db: AsyncSession,
    *,
    email: str,
    password: str,
) -> tuple[User, str, str]:
    """Authenticate credentials, return (user, access_token, raw_refresh_token).
    Same error for 'no such user' and 'wrong password' to prevent enumeration."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    access_token = create_access_token(user.id)
    raw_refresh = await _issue_refresh_token(db, user.id)
    await db.commit()

    return user, access_token, raw_refresh


async def refresh(
    db: AsyncSession,
    *,
    raw_refresh_token: str,
) -> tuple[str, str]:
    """Validate refresh token, rotate it, return (new_access, new_raw_refresh)."""
    token_hash = hash_refresh_token(raw_refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    record = result.scalar_one_or_none()

    if (
        record is None
        or record.revoked
        or record.expires_at < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or expired",
        )

    # Rotation: revoke the old token
    record.revoked = True

    # Issue new pair
    new_access = create_access_token(record.user_id)
    new_raw_refresh = await _issue_refresh_token(db, record.user_id)
    await db.commit()

    return new_access, new_raw_refresh


async def logout(db: AsyncSession, *, raw_refresh_token: str) -> None:
    """Revoke the refresh token so the session is dead."""
    token_hash = hash_refresh_token(raw_refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    record = result.scalar_one_or_none()

    if record is not None:
        record.revoked = True
        await db.commit()


async def _issue_refresh_token(
    db: AsyncSession, user_id: uuid.UUID
) -> str:
    """Create a new refresh token record (hashed), return the raw value."""
    raw_token = generate_refresh_token()
    record = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
        revoked=False,
    )
    db.add(record)
    await db.flush()
    return raw_token
