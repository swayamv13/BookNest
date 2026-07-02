import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Shelf(Base):
    __tablename__ = "shelves"
    __table_args__ = (Index("ix_shelves_owner", "owner_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()"
    )

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="shelves")  # noqa: F821
    # CASCADE here only removes ShelfBook rows (join rows), never Book rows.
    book_links: Mapped[list["ShelfBook"]] = relationship(  # noqa: F821
        back_populates="shelf", cascade="all, delete-orphan"
    )
    shares: Mapped[list["ShelfShare"]] = relationship(  # noqa: F821
        back_populates="shelf", cascade="all, delete-orphan"
    )
