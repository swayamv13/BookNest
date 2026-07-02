import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ActivityLog(Base):
    """Append-only event history. book_id/shelf_id use SET NULL (not CASCADE)
    so a deleted book's history survives -- the event happened, even if its
    subject is gone."""
    __tablename__ = "activity_log"
    __table_args__ = (
        Index("ix_activity_log_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    book_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="SET NULL"),
        nullable=True,
    )
    shelf_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shelves.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_metadata: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()"
    )
