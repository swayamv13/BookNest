"""Custom exception classes and FastAPI exception handlers."""

from fastapi import Request
from fastapi.responses import JSONResponse


class BookNestError(Exception):
    """Base exception for application-level errors."""
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class NotFoundError(BookNestError):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=404)


class ConflictError(BookNestError):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(detail=detail, status_code=409)


class ForbiddenError(BookNestError):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail=detail, status_code=403)


class UnauthorizedError(BookNestError):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail=detail, status_code=401)


class ValidationError(BookNestError):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(detail=detail, status_code=422)


async def booknest_exception_handler(_request: Request, exc: BookNestError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
