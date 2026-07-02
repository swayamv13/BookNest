import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
