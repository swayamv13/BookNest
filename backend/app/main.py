"""BookNest API -- FastAPI entry point.
Registers all routers, CORS, exception handlers, and WebSocket mount."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.exceptions import BookNestError, booknest_exception_handler
from app.routers import auth, books, shelves, lending, dashboard, activity
from app.websocket.router import router as ws_router

app = FastAPI(
    title="BookNest API",
    description="Reading tracker with shared shelves, RBAC, and lending",
    version="1.0.0",
)

# CORS — allow configured origins plus any localhost port in development
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(BookNestError, booknest_exception_handler)

# HTTP routers — lending before books so /books/borrowed and /books/lent-out
# are not captured by /books/{book_id}
app.include_router(auth.router)
app.include_router(lending.router)
app.include_router(books.router)
app.include_router(shelves.router)
app.include_router(dashboard.router)
app.include_router(activity.router)

# WebSocket
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
