"""Lending service -- race-safe lending with partial unique index.
See Section 8.4 of the design document."""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.book import Book
from app.models.user import User
from app.models.lending import Lending
from app.services.activity_service import log_activity
from app.websocket.events import broadcast_book_lent, broadcast_book_returned


async def lend_book(
    db: AsyncSession,
    *,
    owner: User,
    book_id: uuid.UUID,
    borrower_email: str,
) -> Lending:
    # Load book
    book_result = await db.execute(select(Book).where(Book.id == book_id))
    book = book_result.scalar_one_or_none()

    if book is None or book.owner_id != owner.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Load borrower
    borrower_result = await db.execute(
        select(User).where(User.email == borrower_email)
    )
    borrower = borrower_result.scalar_one_or_none()

    if borrower is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="No registered user with that email",
        )

    if borrower.id == owner.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="You cannot lend a book to yourself",
        )

    lending = Lending(
        book_id=book.id, owner_id=owner.id, borrower_id=borrower.id
    )
    db.add(lending)

    try:
        # flush so the unique-index violation surfaces here
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="This book is already lent to someone else",
        )

    await log_activity(
        db,
        user_id=owner.id,
        event_type="book.lent",
        book_id=book.id,
        metadata={
            "borrower_id": str(borrower.id),
            "borrower_email": borrower.email,
        },
    )

    await db.commit()
    await db.refresh(lending)

    # Broadcast only after commit -- clients that re-fetch will see the row
    await broadcast_book_lent(
        owner_id=owner.id,
        borrower_id=borrower.id,
        book_title=book.title,
        borrower_name=borrower.name,
    )

    return lending


async def return_book(
    db: AsyncSession,
    *,
    owner: User,
    book_id: uuid.UUID,
) -> Lending:
    result = await db.execute(
        select(Lending).where(
            Lending.book_id == book_id,
            Lending.owner_id == owner.id,
            Lending.returned_at.is_(None),
        )
    )
    lending = result.scalar_one_or_none()

    if lending is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="No active loan found for this book under your ownership",
        )

    lending.returned_at = datetime.now(timezone.utc)

    await log_activity(
        db,
        user_id=owner.id,
        event_type="book.returned",
        book_id=book_id,
        metadata={"borrower_id": str(lending.borrower_id)},
    )

    await db.commit()
    await db.refresh(lending)

    # Load book title for broadcast
    book_result = await db.execute(select(Book).where(Book.id == book_id))
    book = book_result.scalar_one_or_none()

    await broadcast_book_returned(
        owner_id=owner.id,
        borrower_id=lending.borrower_id,
        book_title=book.title if book else "Unknown",
    )

    return lending


async def get_borrowed_books(
    db: AsyncSession, *, user_id: uuid.UUID
) -> list[Lending]:
    """Books currently lent TO this user."""
    result = await db.execute(
        select(Lending)
        .options(selectinload(Lending.book), selectinload(Lending.owner))
        .where(Lending.borrower_id == user_id, Lending.returned_at.is_(None))
        .order_by(Lending.lent_at.desc())
    )
    return list(result.scalars().all())


async def get_lent_out_books(
    db: AsyncSession, *, user_id: uuid.UUID
) -> list[Lending]:
    """Books this user has lent to others."""
    result = await db.execute(
        select(Lending)
        .options(selectinload(Lending.book), selectinload(Lending.borrower))
        .where(Lending.owner_id == user_id, Lending.returned_at.is_(None))
        .order_by(Lending.lent_at.desc())
    )
    return list(result.scalars().all())
