"""Dashboard service -- aggregate queries for the user's dashboard."""

import uuid
from datetime import date

from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book, BookStatus
from app.models.shelf import Shelf
from app.models.shelf_book import ShelfBook
from app.models.shelf_share import ShelfShare
from app.models.lending import Lending
from app.schemas.dashboard import DashboardResponse


async def get_dashboard(
    db: AsyncSession, *, user_id: uuid.UUID
) -> DashboardResponse:
    # Total books
    total = (
        await db.execute(
            select(func.count()).select_from(Book).where(Book.owner_id == user_id)
        )
    ).scalar() or 0

    # Count by status
    status_counts = {}
    for s in BookStatus:
        count = (
            await db.execute(
                select(func.count())
                .select_from(Book)
                .where(Book.owner_id == user_id, Book.status == s)
            )
        ).scalar() or 0
        status_counts[s] = count

    # Finished this year
    current_year = date.today().year
    finished_this_year = (
        await db.execute(
            select(func.count())
            .select_from(Book)
            .where(
                Book.owner_id == user_id,
                Book.status == BookStatus.FINISHED,
                extract("year", Book.finished_date) == current_year,
            )
        )
    ).scalar() or 0

    # Average rating (of rated books)
    avg_rating = (
        await db.execute(
            select(func.avg(Book.rating)).where(
                Book.owner_id == user_id, Book.rating.is_not(None)
            )
        )
    ).scalar()

    # Shelf with most books
    shelf_q = (
        select(Shelf.name, func.count(ShelfBook.book_id).label("cnt"))
        .join(ShelfBook, ShelfBook.shelf_id == Shelf.id)
        .where(Shelf.owner_id == user_id)
        .group_by(Shelf.id)
        .order_by(func.count(ShelfBook.book_id).desc())
        .limit(1)
    )
    shelf_result = (await db.execute(shelf_q)).first()
    shelf_name = shelf_result[0] if shelf_result else None
    shelf_count = shelf_result[1] if shelf_result else 0

    # Lent out count
    lent_out = (
        await db.execute(
            select(func.count())
            .select_from(Lending)
            .where(Lending.owner_id == user_id, Lending.returned_at.is_(None))
        )
    ).scalar() or 0

    # Borrowed count
    borrowed = (
        await db.execute(
            select(func.count())
            .select_from(Lending)
            .where(Lending.borrower_id == user_id, Lending.returned_at.is_(None))
        )
    ).scalar() or 0

    # Shared with me count
    shared_with_me = (
        await db.execute(
            select(func.count())
            .select_from(ShelfShare)
            .where(ShelfShare.user_id == user_id)
        )
    ).scalar() or 0

    return DashboardResponse(
        total_books=total,
        want_to_read_count=status_counts.get(BookStatus.WANT_TO_READ, 0),
        reading_count=status_counts.get(BookStatus.READING, 0),
        finished_count=status_counts.get(BookStatus.FINISHED, 0),
        finished_this_year=finished_this_year,
        average_rating=round(float(avg_rating), 1) if avg_rating else None,
        shelf_with_most_books=shelf_name,
        shelf_with_most_books_count=shelf_count,
        lent_out_count=lent_out,
        borrowed_count=borrowed,
        shared_with_me_count=shared_with_me,
    )
