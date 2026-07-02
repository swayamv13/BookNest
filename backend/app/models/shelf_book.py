import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ShelfBook(Base):
    """Join table: many-to-many between shelves and books.
    Deleting a shelf cascades here only (membership), never into books.
    Deleting a book cascades here only (removes it from every shelf)."""
    __tablename__ = "shelf_books"

    shelf_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shelves.id", ondelete="CASCADE"),
        primary_key=True,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()"
    )

    shelf: Mapped["Shelf"] = relationship(back_populates="book_links")  # noqa: F821
    book: Mapped["Book"] = relationship(back_populates="shelf_links")  # noqa: F821
