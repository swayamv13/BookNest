from typing import Optional

from pydantic import BaseModel


class DashboardResponse(BaseModel):
    total_books: int = 0
    want_to_read_count: int = 0
    reading_count: int = 0
    finished_count: int = 0
    finished_this_year: int = 0
    average_rating: Optional[float] = None
    shelf_with_most_books: Optional[str] = None
    shelf_with_most_books_count: int = 0
    lent_out_count: int = 0
    borrowed_count: int = 0
    shared_with_me_count: int = 0
