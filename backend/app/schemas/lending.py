import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LendRequest(BaseModel):
    borrower_email: str


class LendingResponse(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    book_title: str
    owner_id: uuid.UUID
    borrower_id: uuid.UUID
    borrower_name: str
    borrower_email: str
    lent_at: datetime
    returned_at: Optional[datetime]

    model_config = {"from_attributes": True}


class BorrowedBookResponse(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    book_title: str
    book_author: str
    owner_name: str
    owner_email: str
    lent_at: datetime

    model_config = {"from_attributes": True}
