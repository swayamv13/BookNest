"""Books router -- CRUD + progress update. See Section 6.2 and 6.4."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.book import BookStatus
from app.schemas.book import (
    BookCreate, BookUpdate, BookResponse, ProgressUpdate, PaginatedBooksResponse,
)
from app.schemas.lending import LendingResponse, BorrowedBookResponse
from app.services import book_service, progress_service, lending_service

router = APIRouter(prefix="/books", tags=["books"])


@router.post("", response_model=BookResponse, status_code=201)
async def create_book(
    data: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = await book_service.create_book(db, owner=current_user, data=data)
    return book


@router.get("", response_model=PaginatedBooksResponse)
async def list_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[BookStatus] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = await book_service.get_books(
        db,
        owner_id=current_user.id,
        page=page,
        page_size=page_size,
        status_filter=status,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return PaginatedBooksResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/borrowed", response_model=list[BorrowedBookResponse])
async def get_borrowed_books(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    loans = await lending_service.get_borrowed_books(db, user_id=current_user.id)
    return [
        BorrowedBookResponse(
            id=l.id,
            book_id=l.book_id,
            book_title=l.book.title,
            book_author=l.book.author,
            owner_name=l.owner.name,
            owner_email=l.owner.email,
            lent_at=l.lent_at,
        )
        for l in loans
    ]


@router.get("/lent-out", response_model=list[LendingResponse])
async def get_lent_out_books(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    loans = await lending_service.get_lent_out_books(db, user_id=current_user.id)
    return [
        LendingResponse(
            id=l.id,
            book_id=l.book_id,
            book_title=l.book.title,
            owner_id=l.owner_id,
            borrower_id=l.borrower_id,
            borrower_name=l.borrower.name,
            borrower_email=l.borrower.email,
            lent_at=l.lent_at,
            returned_at=l.returned_at,
        )
        for l in loans
    ]


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await book_service.get_book(
        db, book_id=book_id, owner_id=current_user.id
    )


@router.patch("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: uuid.UUID,
    data: BookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await book_service.update_book(
        db, book_id=book_id, owner_id=current_user.id, data=data
    )


@router.delete("/{book_id}", status_code=204)
async def delete_book(
    book_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await book_service.delete_book(
        db, book_id=book_id, owner_id=current_user.id
    )


@router.patch("/{book_id}/progress", response_model=BookResponse)
async def update_progress(
    book_id: uuid.UUID,
    data: ProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await progress_service.update_progress(
        db, owner=current_user, book_id=book_id, current_page=data.current_page
    )
