import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings


# ---------------------------------------------------------------------------
# Password hashing (bcrypt -- slow by design, appropriate for human passwords)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


# ---------------------------------------------------------------------------
# Refresh-token hashing (SHA-256 -- fast and deterministic, appropriate for
# high-entropy random tokens that don't need bcrypt's slowness)
# ---------------------------------------------------------------------------

def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


# ---------------------------------------------------------------------------
# JWT access tokens
# ---------------------------------------------------------------------------

def create_access_token(user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> uuid.UUID:
    """Decode and validate an access JWT. Returns the user UUID.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure."""
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Not an access token")
    return uuid.UUID(payload["sub"])
