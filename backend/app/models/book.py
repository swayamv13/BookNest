import uuid
import enum
from datetime import datetime, date

from sqlalchemy import (
    String, Integer, Text, ForeignKey, DateTime, Date,
    CheckConstraint, Index, Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BookStatus(str, enum.Enum):
    WANT_TO_READ = "want_to_read"
    READING = "reading"
    FINISHED = "finished"


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint(
            "rating IS NULL OR (rating BETWEEN 1 AND 5)",
            name="ck_books_rating_range",
        ),
        CheckConstraint(
            "total_pages IS NULL OR total_pages > 0",
            name="ck_books_total_pages_positive",
        ),
        CheckConstraint(
            "current_page IS NULL OR (current_page >= 0 AND "
            "(total_pages IS NULL OR current_page <= total_pages))",
            name="ck_books_current_page_bounds",
        ),
        Index("ix_books_owner_status", "owner_id", "status"),
        Index("ix_books_owner_title", "owner_id", "title"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[BookStatus] = mapped_column(
        SAEnum(
            BookStatus,
            name="book_status",
            values_callable=lambda statuses: [status.value for status in statuses],
        ),
        nullable=False,
        default=BookStatus.WANT_TO_READ,
    )
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_page: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=0
    )
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    finished_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()"
    )

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="books")  # noqa: F821
    shelf_links: Mapped[list["ShelfBook"]] = relationship(  # noqa: F821
        back_populates="book", cascade="all, delete-orphan"
    )
    lending_records: Mapped[list["Lending"]] = relationship(  # noqa: F821
        back_populates="book", cascade="all, delete-orphan"
    )
