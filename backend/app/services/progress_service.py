"""Progress service -- update reading progress with auto-finish detection."""

import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book, BookStatus
from app.models.user import User
from app.services.book_service import get_book
from app.services.activity_service import log_activity


async def update_progress(
    db: AsyncSession,
    *,
    owner: User,
    book_id: uuid.UUID,
    current_page: int,
) -> Book:
    """Update reading progress. Auto-sets status=Finished when done."""
    book = await get_book(db, book_id=book_id, owner_id=owner.id)

    if current_page < 0:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="current_page cannot be negative",
        )

    if book.total_pages is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot track progress without total_pages set",
        )

    if current_page > book.total_pages:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"current_page ({current_page}) exceeds total_pages ({book.total_pages})",
        )

    book.current_page = current_page

    # Auto-finish detection
    if current_page == book.total_pages and book.status != BookStatus.FINISHED:
        book.status = BookStatus.FINISHED
        book.finished_date = date.today()

        await log_activity(
            db,
            user_id=owner.id,
            event_type="book.finished",
            book_id=book.id,
            metadata={"title": book.title},
        )
    else:
        # If we're tracking progress but not finished, ensure status is READING
        if book.status == BookStatus.WANT_TO_READ and current_page > 0:
            book.status = BookStatus.READING

        await log_activity(
            db,
            user_id=owner.id,
            event_type="book.progress_updated",
            book_id=book.id,
            metadata={
                "current_page": current_page,
                "total_pages": book.total_pages,
            },
        )

    await db.commit()
    await db.refresh(book)
    return book
