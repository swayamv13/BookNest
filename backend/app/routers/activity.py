"""Activity router -- GET /activity (paginated). See Section 6.4."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.activity import ActivityResponse, PaginatedActivityResponse
from app.services import activity_service

router = APIRouter(tags=["activity"])


@router.get("/activity", response_model=PaginatedActivityResponse)
async def get_activity(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = await activity_service.get_user_activity(
        db, user_id=current_user.id, page=page, page_size=page_size
    )
    return PaginatedActivityResponse(
        items=items, total=total, page=page, page_size=page_size
    )
