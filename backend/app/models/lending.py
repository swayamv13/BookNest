import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Lending(Base):
    """One row per loan. returned_at IS NULL means the loan is currently active.
    The partial unique index (created in migration) guarantees at most one
    active loan per book at the database level."""
    __tablename__ = "lending"
    __table_args__ = (
        CheckConstraint("owner_id <> borrower_id", name="ck_lending_owner_not_borrower"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    lent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()"
    )
    returned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    book: Mapped["Book"] = relationship(back_populates="lending_records")  # noqa: F821
    owner: Mapped["User"] = relationship(foreign_keys=[owner_id])  # noqa: F821
    borrower: Mapped["User"] = relationship(foreign_keys=[borrower_id])  # noqa: F821
