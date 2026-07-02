"""Auth router -- signup, login, refresh, logout.
Refresh token set as httpOnly, Secure, SameSite=Strict cookie."""

from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, AuthResponse, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = "refresh_token"
COOKIE_MAX_AGE = 14 * 24 * 60 * 60  # 14 days in seconds


def _cookie_options():
    """httpOnly refresh cookie flags."""
    if settings.is_production:
        return {"secure": True, "samesite": "lax"}
    return {"secure": False, "samesite": "lax"}


def _set_refresh_cookie(response: Response, raw_token: str):
    opts = _cookie_options()
    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=opts["secure"],
        samesite=opts["samesite"],
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


def _clear_refresh_cookie(response: Response):
    opts = _cookie_options()
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        secure=opts["secure"],
        samesite=opts["samesite"],
    )


@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(
    data: SignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user, access_token, raw_refresh = await auth_service.signup(
        db, name=data.name, email=data.email, password=data.password
    )
    _set_refresh_cookie(response, raw_refresh)
    return AuthResponse(access_token=access_token, user=user)


@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user, access_token, raw_refresh = await auth_service.login(
        db, email=data.email, password=data.password
    )
    _set_refresh_cookie(response, raw_refresh)
    return AuthResponse(access_token=access_token, user=user)


@router.post("/refresh", response_model=TokenResponse, responses={204: {"description": "No active session"}})
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    raw_refresh = request.cookies.get(COOKIE_NAME)
    if not raw_refresh:
        return Response(status_code=204)

    new_access, new_raw_refresh = await auth_service.refresh(
        db, raw_refresh_token=raw_refresh
    )
    _set_refresh_cookie(response, new_raw_refresh)
    return TokenResponse(access_token=new_access)


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    raw_refresh = request.cookies.get(COOKIE_NAME)
    if raw_refresh:
        await auth_service.logout(db, raw_refresh_token=raw_refresh)
    _clear_refresh_cookie(response)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
