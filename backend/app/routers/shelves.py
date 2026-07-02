"""Shelves router -- CRUD, book management, sharing. Every route uses
the RBAC dependency. See Section 6.3."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.shelf_access import (
    require_shelf_access, require_shelf_owner,
    EffectiveRole, ShelfAccessResult,
)
from app.models.user import User
from app.schemas.shelf import (
    ShelfCreate, ShelfUpdate, ShelfResponse, ShelfDetailResponse,
    ShareRequest, ShareUpdate, CollaboratorResponse,
)
from app.schemas.book import BookResponse
from app.services import shelf_service

router = APIRouter(prefix="/shelves", tags=["shelves"])


@router.post("", response_model=ShelfResponse, status_code=201)
async def create_shelf(
    data: ShelfCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    shelf = await shelf_service.create_shelf(db, owner=current_user, data=data)
    return ShelfResponse(
        id=shelf.id,
        owner_id=shelf.owner_id,
        name=shelf.name,
        created_at=shelf.created_at,
        book_count=0,
        role="owner",
    )


@router.get("", response_model=list[ShelfResponse])
async def list_own_shelves(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await shelf_service.get_own_shelves(db, owner_id=current_user.id)


@router.get("/shared-with-me", response_model=list[ShelfResponse])
async def list_shared_shelves(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await shelf_service.get_shared_shelves(db, user_id=current_user.id)


@router.get("/{shelf_id}", response_model=ShelfDetailResponse)
async def get_shelf(
    shelf_id: uuid.UUID,
    access: ShelfAccessResult = Depends(
        require_shelf_access(EffectiveRole.VIEWER)
    ),
    db: AsyncSession = Depends(get_db),
):
    detail = await shelf_service.get_shelf_detail(db, shelf=access.shelf)
    detail["role"] = access.effective_role.name.lower()
    return detail


@router.patch("/{shelf_id}", response_model=ShelfResponse)
async def update_shelf(
    shelf_id: uuid.UUID,
    data: ShelfUpdate,
    access: ShelfAccessResult = Depends(require_shelf_owner()),
    db: AsyncSession = Depends(get_db),
):
    shelf = await shelf_service.update_shelf(db, shelf=access.shelf, data=data)
    return ShelfResponse(
        id=shelf.id,
        owner_id=shelf.owner_id,
        name=shelf.name,
        created_at=shelf.created_at,
        book_count=0,
        role="owner",
    )


@router.delete("/{shelf_id}", status_code=204)
async def delete_shelf(
    shelf_id: uuid.UUID,
    access: ShelfAccessResult = Depends(require_shelf_owner()),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await shelf_service.delete_shelf(
        db, shelf=access.shelf, owner_id=current_user.id
    )


# ---- Book management on shelves ----

@router.post("/{shelf_id}/books/{book_id}", status_code=201)
async def add_book_to_shelf(
    shelf_id: uuid.UUID,
    book_id: uuid.UUID,
    access: ShelfAccessResult = Depends(
        require_shelf_access(EffectiveRole.EDITOR)
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await shelf_service.add_book_to_shelf(
        db, shelf=access.shelf, book_id=book_id, user=current_user
    )
    return {"detail": "Book added to shelf"}


@router.delete("/{shelf_id}/books/{book_id}", status_code=204)
async def remove_book_from_shelf(
    shelf_id: uuid.UUID,
    book_id: uuid.UUID,
    access: ShelfAccessResult = Depends(
        require_shelf_access(EffectiveRole.EDITOR)
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await shelf_service.remove_book_from_shelf(
        db, shelf=access.shelf, book_id=book_id, user=current_user
    )


# ---- Sharing ----

@router.post("/{shelf_id}/share", response_model=CollaboratorResponse, status_code=201)
async def share_shelf(
    shelf_id: uuid.UUID,
    data: ShareRequest,
    access: ShelfAccessResult = Depends(require_shelf_owner()),
    db: AsyncSession = Depends(get_db),
):
    share = await shelf_service.share_shelf(
        db, shelf=access.shelf, email=data.email, role=data.role
    )
    # Reload user info
    from sqlalchemy import select
    from app.models.user import User as UserModel
    user_result = await db.execute(
        select(UserModel).where(UserModel.id == share.user_id)
    )
    user = user_result.scalar_one()
    return CollaboratorResponse(
        id=share.id,
        user_id=share.user_id,
        user_name=user.name,
        user_email=user.email,
        role=share.role,
        created_at=share.created_at,
    )


@router.patch("/{shelf_id}/share/{user_id}")
async def update_share(
    shelf_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ShareUpdate,
    access: ShelfAccessResult = Depends(require_shelf_owner()),
    db: AsyncSession = Depends(get_db),
):
    share = await shelf_service.update_share(
        db, shelf=access.shelf, user_id=user_id, role=data.role
    )
    return {"detail": "Role updated", "role": share.role.value}


@router.delete("/{shelf_id}/share/{user_id}", status_code=204)
async def remove_share(
    shelf_id: uuid.UUID,
    user_id: uuid.UUID,
    access: ShelfAccessResult = Depends(require_shelf_owner()),
    db: AsyncSession = Depends(get_db),
):
    await shelf_service.remove_share(
        db, shelf=access.shelf, user_id=user_id
    )
