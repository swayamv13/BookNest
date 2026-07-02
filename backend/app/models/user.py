import uuid
import enum
from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()"
    )

    # Relationships
    books: Mapped[list["Book"]] = relationship(  # noqa: F821
        back_populates="owner", cascade="all, delete-orphan"
    )
    shelves: Mapped[list["Shelf"]] = relationship(  # noqa: F821
        back_populates="owner", cascade="all, delete-orphan"
    )
