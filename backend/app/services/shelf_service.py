"""Shelf service -- CRUD, book management, sharing, with WebSocket broadcasts."""

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.book import Book
from app.models.shelf import Shelf
from app.models.shelf_book import ShelfBook
from app.models.shelf_share import ShelfShare, ShelfRole
from app.models.user import User
from app.schemas.shelf import ShelfCreate, ShelfUpdate, ShareRequest
from app.services.activity_service import log_activity
from app.websocket.events import broadcast_shelf_book_added, broadcast_shelf_book_removed


async def create_shelf(
    db: AsyncSession, *, owner: User, data: ShelfCreate
) -> Shelf:
    shelf = Shelf(owner_id=owner.id, name=data.name)
    db.add(shelf)
    await db.flush()

    await log_activity(
        db,
        user_id=owner.id,
        event_type="shelf.created",
        shelf_id=shelf.id,
        metadata={"name": shelf.name},
    )

    await db.commit()
    await db.refresh(shelf)
    return shelf


async def get_own_shelves(
    db: AsyncSession, *, owner_id: uuid.UUID
) -> list[dict]:
    """Return shelves owned by this user, with book counts."""
    result = await db.execute(
        select(Shelf)
        .options(selectinload(Shelf.book_links))
        .where(Shelf.owner_id == owner_id)
        .order_by(Shelf.created_at.desc())
    )
    shelves = result.scalars().all()
    return [
        {
            "id": s.id,
            "owner_id": s.owner_id,
            "name": s.name,
            "created_at": s.created_at,
            "book_count": len(s.book_links),
            "role": "owner",
        }
        for s in shelves
    ]


async def get_shared_shelves(
    db: AsyncSession, *, user_id: uuid.UUID
) -> list[dict]:
    """Return shelves shared with this user, with their role."""
    result = await db.execute(
        select(ShelfShare)
        .options(selectinload(ShelfShare.shelf).selectinload(Shelf.book_links))
        .where(ShelfShare.user_id == user_id)
        .order_by(ShelfShare.created_at.desc())
    )
    shares = result.scalars().all()
    return [
        {
            "id": share.shelf.id,
            "owner_id": share.shelf.owner_id,
            "name": share.shelf.name,
            "created_at": share.shelf.created_at,
            "book_count": len(share.shelf.book_links),
            "role": share.role.value,
        }
        for share in shares
    ]


async def get_shelf_detail(
    db: AsyncSession, *, shelf: Shelf
) -> dict:
    """Return full shelf detail with books and collaborators."""
    # Load books via join table
    result = await db.execute(
        select(ShelfBook)
        .options(selectinload(ShelfBook.book))
        .where(ShelfBook.shelf_id == shelf.id)
        .order_by(ShelfBook.added_at.desc())
    )
    shelf_books = result.scalars().all()
    books = [sb.book for sb in shelf_books]

    # Load collaborators
    shares_result = await db.execute(
        select(ShelfShare)
        .options(selectinload(ShelfShare.user))
        .where(ShelfShare.shelf_id == shelf.id)
    )
    shares = shares_result.scalars().all()

    # Load owner
    owner_result = await db.execute(select(User).where(User.id == shelf.owner_id))
    owner = owner_result.scalar_one()

    collaborators = [
        {
            "id": s.id,
            "user_id": s.user_id,
            "user_name": s.user.name,
            "user_email": s.user.email,
            "role": s.role,
            "created_at": s.created_at,
        }
        for s in shares
    ]

    return {
        "id": shelf.id,
        "owner_id": shelf.owner_id,
        "owner_name": owner.name,
        "name": shelf.name,
        "created_at": shelf.created_at,
        "books": books,
        "collaborators": collaborators,
    }


async def update_shelf(
    db: AsyncSession, *, shelf: Shelf, data: ShelfUpdate
) -> Shelf:
    shelf.name = data.name
    await db.commit()
    await db.refresh(shelf)
    return shelf


async def delete_shelf(
    db: AsyncSession, *, shelf: Shelf, owner_id: uuid.UUID
) -> None:
    await log_activity(
        db,
        user_id=owner_id,
        event_type="shelf.deleted",
        shelf_id=shelf.id,
        metadata={"name": shelf.name},
    )
    await db.delete(shelf)
    await db.commit()


async def add_book_to_shelf(
    db: AsyncSession,
    *,
    shelf: Shelf,
    book_id: uuid.UUID,
    user: User,
) -> ShelfBook:
    """Add a book to a shelf. Book must exist and belong to shelf owner
    or the acting user."""
    book_result = await db.execute(select(Book).where(Book.id == book_id))
    book = book_result.scalar_one_or_none()

    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Check if already on shelf
    existing = await db.execute(
        select(ShelfBook).where(
            ShelfBook.shelf_id == shelf.id, ShelfBook.book_id == book_id
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Book is already on this shelf"
        )

    link = ShelfBook(shelf_id=shelf.id, book_id=book_id)
    db.add(link)

    await log_activity(
        db,
        user_id=user.id,
        event_type="shelf.book_added",
        shelf_id=shelf.id,
        book_id=book_id,
        metadata={"book_title": book.title, "shelf_name": shelf.name},
    )

    await db.commit()
    await db.refresh(link)

    # Broadcast after commit
    await broadcast_shelf_book_added(
        db, shelf_id=shelf.id, book_title=book.title, shelf_name=shelf.name
    )

    return link


async def remove_book_from_shelf(
    db: AsyncSession,
    *,
    shelf: Shelf,
    book_id: uuid.UUID,
    user: User,
) -> None:
    result = await db.execute(
        select(ShelfBook).where(
            ShelfBook.shelf_id == shelf.id, ShelfBook.book_id == book_id
        )
    )
    link = result.scalar_one_or_none()

    if link is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Book not found on this shelf"
        )

    # Get book title before removal
    book_result = await db.execute(select(Book).where(Book.id == book_id))
    book = book_result.scalar_one_or_none()
    book_title = book.title if book else "Unknown"

    await db.delete(link)

    await log_activity(
        db,
        user_id=user.id,
        event_type="shelf.book_removed",
        shelf_id=shelf.id,
        book_id=book_id,
        metadata={"book_title": book_title, "shelf_name": shelf.name},
    )

    await db.commit()

    await broadcast_shelf_book_removed(
        db, shelf_id=shelf.id, book_title=book_title, shelf_name=shelf.name
    )


async def share_shelf(
    db: AsyncSession,
    *,
    shelf: Shelf,
    email: str,
    role: ShelfRole,
) -> ShelfShare:
    """Share a shelf with a user by email. Upserts the role."""
    user_result = await db.execute(select(User).where(User.email == email))
    target_user = user_result.scalar_one_or_none()

    if target_user is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="No registered user with that email",
        )

    if target_user.id == shelf.owner_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Cannot share a shelf with its owner",
        )

    # Upsert
    existing_result = await db.execute(
        select(ShelfShare).where(
            ShelfShare.shelf_id == shelf.id,
            ShelfShare.user_id == target_user.id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.role = role
        share = existing
    else:
        share = ShelfShare(
            shelf_id=shelf.id, user_id=target_user.id, role=role
        )
        db.add(share)

    await db.flush()

    await log_activity(
        db,
        user_id=shelf.owner_id,
        event_type="shelf.shared",
        shelf_id=shelf.id,
        metadata={
            "shared_with": email,
            "role": role.value,
            "shelf_name": shelf.name,
        },
    )

    await db.commit()
    await db.refresh(share)
    return share


async def update_share(
    db: AsyncSession,
    *,
    shelf: Shelf,
    user_id: uuid.UUID,
    role: ShelfRole,
) -> ShelfShare:
    result = await db.execute(
        select(ShelfShare).where(
            ShelfShare.shelf_id == shelf.id,
            ShelfShare.user_id == user_id,
        )
    )
    share = result.scalar_one_or_none()

    if share is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Collaborator not found"
        )

    share.role = role
    await db.commit()
    await db.refresh(share)
    return share


async def remove_share(
    db: AsyncSession,
    *,
    shelf: Shelf,
    user_id: uuid.UUID,
) -> None:
    result = await db.execute(
        select(ShelfShare).where(
            ShelfShare.shelf_id == shelf.id,
            ShelfShare.user_id == user_id,
        )
    )
    share = result.scalar_one_or_none()

    if share is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Collaborator not found"
        )

    await db.delete(share)
    await db.commit()
