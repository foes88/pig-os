from pydantic import BaseModel, EmailStr, Field

USERNAME_PATTERN = r"^[a-zA-Z0-9_.-]{3,50}$"  # 영숫자·_.- 3~50자


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., pattern=USERNAME_PATTERN, description="로그인 아이디(영숫자·_.-)")
    email: EmailStr  # 복구·연락용 필수(unique)
    password: str = Field(..., min_length=8)
    org_name: str = Field(..., min_length=1, max_length=200)
    country: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    timezone: str = Field(default="UTC")
    language: str = Field(default="en")


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)  # 아이디 로그인(email 아님)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class LoginResponse(TokenResponse):
    user_id: str
    name: str
    username: str
    email: str
    role: str
    farm_ids: list[str]


class OnboardingCompleteRequest(BaseModel):
    org_name: str = Field(..., min_length=1, max_length=200)
    country: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    name: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., pattern=USERNAME_PATTERN, description="로그인 아이디")
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
    username: str
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
