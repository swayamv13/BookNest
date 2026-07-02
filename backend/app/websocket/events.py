"""Typed event builders and scoping logic.
Each broadcast function computes the exact set of users who should receive
the event, then sends only to those connections."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shelf_share import ShelfShare
from app.models.shelf import Shelf
from app.websocket.manager import manager


async def broadcast_book_lent(
    *, owner_id: uuid.UUID, borrower_id: uuid.UUID, book_title: str, borrower_name: str
):
    """Sent to both the book owner and the borrower."""
    event = {
        "type": "book.lent",
        "data": {
            "book_title": book_title,
            "borrower_name": borrower_name,
            "owner_id": str(owner_id),
            "borrower_id": str(borrower_id),
        },
    }
    await manager.send_to_users([owner_id, borrower_id], event)


async def broadcast_book_returned(
    *, owner_id: uuid.UUID, borrower_id: uuid.UUID, book_title: str
):
    """Sent to both the book owner and the borrower."""
    event = {
        "type": "book.returned",
        "data": {
            "book_title": book_title,
            "owner_id": str(owner_id),
            "borrower_id": str(borrower_id),
        },
    }
    await manager.send_to_users([owner_id, borrower_id], event)


async def _get_shelf_audience(db: AsyncSession, shelf_id: uuid.UUID) -> list[uuid.UUID]:
    """Compute the set of users who should receive shelf events:
    the shelf owner + every collaborator."""
    shelf_result = await db.execute(select(Shelf).where(Shelf.id == shelf_id))
    shelf = shelf_result.scalar_one_or_none()
    if shelf is None:
        return []

    user_ids = [shelf.owner_id]

    shares_result = await db.execute(
        select(ShelfShare.user_id).where(ShelfShare.shelf_id == shelf_id)
    )
    for row in shares_result:
        user_ids.append(row[0])

    return user_ids


async def broadcast_shelf_book_added(
    db: AsyncSession, *, shelf_id: uuid.UUID, book_title: str, shelf_name: str
):
    """Sent to shelf owner + every collaborator."""
    audience = await _get_shelf_audience(db, shelf_id)
    event = {
        "type": "shelf.book_added",
        "data": {
            "shelf_id": str(shelf_id),
            "shelf_name": shelf_name,
            "book_title": book_title,
        },
    }
    await manager.send_to_users(audience, event)


async def broadcast_shelf_book_removed(
    db: AsyncSession, *, shelf_id: uuid.UUID, book_title: str, shelf_name: str
):
    """Sent to shelf owner + every collaborator."""
    audience = await _get_shelf_audience(db, shelf_id)
    event = {
        "type": "shelf.book_removed",
        "data": {
            "shelf_id": str(shelf_id),
            "shelf_name": shelf_name,
            "book_title": book_title,
        },
    }
    await manager.send_to_users(audience, event)


async def broadcast_activity(user_id: uuid.UUID, activity_data: dict):
    """Sent to the user the event belongs to."""
    event = {"type": "activity.new", "data": activity_data}
    await manager.send_to_user(user_id, event)
