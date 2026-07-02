import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ActivityResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    event_type: str
    book_id: Optional[uuid.UUID]
    shelf_id: Optional[uuid.UUID]
    event_metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedActivityResponse(BaseModel):
    items: list[ActivityResponse]
    total: int
    page: int
    page_size: int
