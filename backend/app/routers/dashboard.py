"""Dashboard router -- GET /dashboard. See Section 6.4."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard_service

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await dashboard_service.get_dashboard(db, user_id=current_user.id)
