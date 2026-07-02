import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RefreshToken(Base):
    """Stores a HASH of the refresh token, never the raw value -- same
    principle as password storage. Lets us revoke individual sessions."""
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_tokens_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()"
    )
