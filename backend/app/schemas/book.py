import uuid
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field

from app.models.book import BookStatus


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=300)
    status: BookStatus = BookStatus.WANT_TO_READ
    total_pages: Optional[int] = Field(None, gt=0)
    current_page: Optional[int] = Field(0, ge=0)
    rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    author: Optional[str] = Field(None, min_length=1, max_length=300)
    status: Optional[BookStatus] = None
    total_pages: Optional[int] = Field(None, gt=0)
    rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class BookResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    author: str
    status: BookStatus
    total_pages: Optional[int]
    current_page: Optional[int]
    rating: Optional[int]
    notes: Optional[str]
    finished_date: Optional[date]
    created_at: datetime

    model_config = {"from_attributes": True}


class ProgressUpdate(BaseModel):
    current_page: int = Field(..., ge=0)


class PaginatedBooksResponse(BaseModel):
    items: list[BookResponse]
    total: int
    page: int
    page_size: int
