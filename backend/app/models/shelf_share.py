import uuid
import enum
from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, UniqueConstraint, Enum as SAEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ShelfRole(str, enum.Enum):
    EDITOR = "editor"
    VIEWER = "viewer"


class ShelfShare(Base):
    """RBAC table: who has what role on which shelf.
    Owner is NOT a row here -- ownership lives on shelves.owner_id.
    This table is collaborators only."""
    __tablename__ = "shelf_shares"
    __table_args__ = (
        UniqueConstraint("shelf_id", "user_id", name="uq_shelf_shares_shelf_user"),
        Index("ix_shelf_shares_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    shelf_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shelves.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[ShelfRole] = mapped_column(
        SAEnum(
            ShelfRole,
            name="shelf_role",
            values_callable=lambda roles: [role.value for role in roles],
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()"
    )

    shelf: Mapped["Shelf"] = relationship(back_populates="shares")  # noqa: F821
    user: Mapped["User"] = relationship()  # noqa: F821
