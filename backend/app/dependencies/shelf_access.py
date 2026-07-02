"""The single chokepoint for shelf RBAC. Every shelf-scoped route declares
its required role via this dependency instead of writing its own permission
check. See Section 4 and 8.3 of the design document."""

import uuid
from enum import IntEnum

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.shelf import Shelf
from app.models.shelf_share import ShelfShare, ShelfRole


class EffectiveRole(IntEnum):
    """Ordered so 'minimum role' comparisons (>=) work naturally.
    Owner outranks editor outranks viewer."""
    VIEWER = 1
    EDITOR = 2
    OWNER = 3


def _role_to_effective(role: ShelfRole) -> EffectiveRole:
    return EffectiveRole.EDITOR if role == ShelfRole.EDITOR else EffectiveRole.VIEWER


class ShelfAccessResult:
    """Returned to the route so it can use the already-loaded shelf and
    role without a second query."""
    def __init__(self, shelf: Shelf, effective_role: EffectiveRole):
        self.shelf = shelf
        self.effective_role = effective_role


def require_shelf_access(min_role: EffectiveRole):
    """Factory: returns a FastAPI dependency requiring at least `min_role`
    on the shelf identified by the `shelf_id` path parameter.

    Usage in a router:
        @router.post("/shelves/{shelf_id}/books/{book_id}")
        async def add_book(
            shelf_id: uuid.UUID,
            book_id: uuid.UUID,
            access: ShelfAccessResult = Depends(
                require_shelf_access(EffectiveRole.EDITOR)
            ),
            ...
        ):
            ...
    """

    async def _dependency(
        shelf_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> ShelfAccessResult:
        result = await db.execute(select(Shelf).where(Shelf.id == shelf_id))
        shelf = result.scalar_one_or_none()

        # Deliberately 404, not 403, when the shelf doesn't exist OR the
        # user has zero access -- avoids leaking shelf existence.
        if shelf is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="Shelf not found"
            )

        # Owner gets full access immediately -- no share lookup needed.
        if shelf.owner_id == current_user.id:
            return ShelfAccessResult(shelf=shelf, effective_role=EffectiveRole.OWNER)

        share_result = await db.execute(
            select(ShelfShare).where(
                ShelfShare.shelf_id == shelf_id,
                ShelfShare.user_id == current_user.id,
            )
        )
        share = share_result.scalar_one_or_none()

        if share is None:
            # No relationship to this shelf -- same 404 treatment.
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="Shelf not found"
            )

        effective = _role_to_effective(share.role)

        if effective < min_role:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=(
                    f"This action requires {min_role.name.lower()} access; "
                    f"you have {effective.name.lower()}"
                ),
            )

        return ShelfAccessResult(shelf=shelf, effective_role=effective)

    return _dependency


def require_shelf_owner():
    """Convenience wrapper for owner-only actions: share, change role,
    remove collaborator, delete shelf."""
    return require_shelf_access(EffectiveRole.OWNER)
