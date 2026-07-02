import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.shelf_share import ShelfRole
from app.schemas.book import BookResponse


class ShelfCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class ShelfUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class ShelfResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    created_at: datetime
    book_count: int = 0
    role: str = "owner"

    model_config = {"from_attributes": True}


class CollaboratorResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    user_email: str
    role: ShelfRole
    created_at: datetime


class ShelfDetailResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    owner_name: str
    name: str
    created_at: datetime
    books: list[BookResponse]
    collaborators: list[CollaboratorResponse]
    role: str = "owner"


class ShareRequest(BaseModel):
    email: str
    role: ShelfRole


class ShareUpdate(BaseModel):
    role: ShelfRole
