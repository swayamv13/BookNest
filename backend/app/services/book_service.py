"""Book service -- CRUD with ownership enforcement, server-side
pagination, filtering, and sorting."""

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book, BookStatus
from app.models.user import User
from app.schemas.book import BookCreate, BookUpdate
from app.services.activity_service import log_activity


async def create_book(
    db: AsyncSession, *, owner: User, data: BookCreate
) -> Book:
    book = Book(
        owner_id=owner.id,
        title=data.title,
        author=data.author,
        status=data.status,
        total_pages=data.total_pages,
        current_page=data.current_page or 0,
        rating=data.rating,
        notes=data.notes,
    )
    db.add(book)
    await db.flush()

    await log_activity(
        db,
        user_id=owner.id,
        event_type="book.created",
        book_id=book.id,
        metadata={"title": book.title},
    )

    await db.commit()
    await db.refresh(book)
    return book


async def get_books(
    db: AsyncSession,
    *,
    owner_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[BookStatus] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> tuple[list[Book], int]:
    """Own books only, with filtering, search, sorting, and pagination."""
    base = select(Book).where(Book.owner_id == owner_id)

    if status_filter:
        base = base.where(Book.status == status_filter)

    if search:
        pattern = f"%{search}%"
        base = base.where(
            or_(Book.title.ilike(pattern), Book.author.ilike(pattern))
        )

    # Count total
    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Sorting
    sort_column = getattr(Book, sort_by, Book.created_at)
    if sort_dir == "asc":
        base = base.order_by(sort_column.asc())
    else:
        base = base.order_by(sort_column.desc())

    # Pagination
    offset = (page - 1) * page_size
    base = base.offset(offset).limit(page_size)

    result = await db.execute(base)
    items = list(result.scalars().all())
    return items, total


async def get_book(
    db: AsyncSession, *, book_id: uuid.UUID, owner_id: uuid.UUID
) -> Book:
    """Get a single book. Returns 404 if not owner (don't leak existence)."""
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()

    if book is None or book.owner_id != owner_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Book not found")

    return book


async def update_book(
    db: AsyncSession,
    *,
    book_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: BookUpdate,
) -> Book:
    book = await get_book(db, book_id=book_id, owner_id=owner_id)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(book, key, value)

    await log_activity(
        db,
        user_id=owner_id,
        event_type="book.updated",
        book_id=book.id,
        metadata={"fields": list(update_data.keys())},
    )

    await db.commit()
    await db.refresh(book)
    return book


async def delete_book(
    db: AsyncSession, *, book_id: uuid.UUID, owner_id: uuid.UUID
) -> None:
    book = await get_book(db, book_id=book_id, owner_id=owner_id)

    await log_activity(
        db,
        user_id=owner_id,
        event_type="book.deleted",
        book_id=book.id,
        metadata={"title": book.title},
    )

    await db.delete(book)
    await db.commit()
