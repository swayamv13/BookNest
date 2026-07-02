"""Lending router -- lend, return, borrowed, lent-out. See Section 6.4."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.lending import LendRequest, LendingResponse
from app.services import lending_service

router = APIRouter(prefix="/books", tags=["lending"])


@router.post("/{book_id}/lend", response_model=LendingResponse, status_code=201)
async def lend_book(
    book_id: uuid.UUID,
    data: LendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lending = await lending_service.lend_book(
        db, owner=current_user, book_id=book_id, borrower_email=data.borrower_email
    )
    # Reload relationships
    await db.refresh(lending, ["book", "borrower"])
    return LendingResponse(
        id=lending.id,
        book_id=lending.book_id,
        book_title=lending.book.title,
        owner_id=lending.owner_id,
        borrower_id=lending.borrower_id,
        borrower_name=lending.borrower.name,
        borrower_email=lending.borrower.email,
        lent_at=lending.lent_at,
        returned_at=lending.returned_at,
    )


@router.post("/{book_id}/return", response_model=LendingResponse)
async def return_book(
    book_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lending = await lending_service.return_book(
        db, owner=current_user, book_id=book_id
    )
    await db.refresh(lending, ["book", "borrower"])
    return LendingResponse(
        id=lending.id,
        book_id=lending.book_id,
        book_title=lending.book.title,
        owner_id=lending.owner_id,
        borrower_id=lending.borrower_id,
        borrower_name=lending.borrower.name,
        borrower_email=lending.borrower.email,
        lent_at=lending.lent_at,
        returned_at=lending.returned_at,
    )
