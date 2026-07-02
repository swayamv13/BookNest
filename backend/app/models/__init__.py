"""ORM models -- import all models here so Alembic and other
consumers can do a single `from app.models import Base`."""

from app.database import Base  # noqa: F401

from app.models.user import User  # noqa: F401
from app.models.book import Book, BookStatus  # noqa: F401
from app.models.shelf import Shelf  # noqa: F401
from app.models.shelf_book import ShelfBook  # noqa: F401
from app.models.shelf_share import ShelfShare, ShelfRole  # noqa: F401
from app.models.lending import Lending  # noqa: F401
from app.models.activity_log import ActivityLog  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
