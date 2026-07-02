from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_ENV_FILE = _BACKEND_DIR / ".env"


def _normalize_database_url(url: str) -> str:
    """PostgreSQL URLs from hosting providers may use postgresql:// — async needs +asyncpg."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://booknest:booknest_dev@localhost:5433/booknest"
    jwt_secret: str = "change-me-to-a-long-random-secret-string"
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 14
    is_production: bool = False

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_db_url(cls, v: str) -> str:
        return _normalize_database_url(v)

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8"}


settings = Settings()
