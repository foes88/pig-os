from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    org_name: str = Field(..., min_length=1, max_length=200)
    country: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    timezone: str = Field(default="UTC")
    language: str = Field(default="en")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class LoginResponse(TokenResponse):
    user_id: str
    name: str
    email: str
    role: str
    farm_ids: list[str]


class OnboardingCompleteRequest(BaseModel):
    org_name: str = Field(..., min_length=1, max_length=200)
    country: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    farm_name: str = Field(..., min_length=1, max_length=200)
    farm_type: str = Field(default="FARROW_TO_FINISH")
    sow_count: int | None = Field(default=None, ge=1)
    timezone: str = Field(default="UTC")


class OnboardingCompleteResponse(BaseModel):
    org_id: str
    farm_id: str
    user_id: str
    access_token: str
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class MeResponse(BaseModel):
    id: str
    name: str
    email: str | None
    role: str
    org_id: str | None
    language: str
    farm_ids: list[str]


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
