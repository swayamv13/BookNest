"""Activity log service -- append-only writes and paginated retrieval."""

import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.websocket.events import broadcast_activity


async def log_activity(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    event_type: str,
    book_id: Optional[uuid.UUID] = None,
    shelf_id: Optional[uuid.UUID] = None,
    metadata: Optional[dict] = None,
) -> ActivityLog:
    """Append an event to the activity log."""
    entry = ActivityLog(
        user_id=user_id,
        event_type=event_type,
        book_id=book_id,
        shelf_id=shelf_id,
        event_metadata=metadata or {},
    )
    db.add(entry)
    await db.flush()
    return entry


async def get_user_activity(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ActivityLog], int]:
    """Paginated, reverse-chronological activity for a user."""
    count_q = select(func.count()).select_from(ActivityLog).where(
        ActivityLog.user_id == user_id
    )
    total = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * page_size
    items_q = (
        select(ActivityLog)
        .where(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(items_q)
    items = list(result.scalars().all())

    return items, total
