from pydantic import BaseModel, EmailStr, Field, field_validator

USERNAME_PATTERN = r"^[a-zA-Z0-9_.-]{3,50}$"  # 영숫자·_.- 3~50자

# 사칭·혼동 방지 — 로그인 아이디로 쓸 수 없는 예약어(대소문자·leetspeak 무관)
_RESERVED_USERNAMES = {
    "admin", "administrator", "root", "superuser", "superadmin", "super_admin",
    "system", "sysadmin", "support", "helpdesk", "info", "contact", "moderator",
    "mod", "staff", "operator", "owner", "master", "official", "security",
    "billing", "api", "www", "pigos", "pigplan", "wiselake", "null", "undefined",
}
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "@": "a", "$": "s"})


def validate_username_not_reserved(v: str) -> str:
    """예약어/브랜드/권한어 사칭 아이디 거부(admin·administrator·pigos 등, leet 변형 포함)."""
    norm = v.strip().lower().translate(_LEET)
    if (
        norm in _RESERVED_USERNAMES
        or norm.startswith("admin")
        or any(b in norm for b in ("administrator", "pigos", "wiselake", "superadmin"))
    ):
        raise ValueError("This username is reserved and cannot be used")
    return v


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., pattern=USERNAME_PATTERN, description="로그인 아이디(영숫자·_.-)")
    email: EmailStr  # 복구·연락용 필수(unique)
    password: str = Field(..., min_length=8)
    org_name: str = Field(..., min_length=1, max_length=200)
    country: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    timezone: str = Field(default="UTC")
    language: str = Field(default="en")

    @field_validator("username")
    @classmethod
    def _no_reserved_username(cls, v: str) -> str:
        return validate_username_not_reserved(v)


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
    system_role: str = "FARM_OWNER"  # 플랫폼 권한 기준(백엔드 effective_system_role) — 관리자 UI 게이팅용
    farm_ids: list[str]
    farm_roles: dict[str, str] = {}  # farm_id → 농장별 유효 role (멀티팜 게이팅용)


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
    language: str = Field(default="en")  # 온보딩 로케일 보존(M3: 하드코딩 "en" 제거)
    # 국가별 파생값 — 클라가 안 보내면 서버가 country_config에서 채움(단일 소스).
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    unit_system: str | None = Field(default=None, pattern="^(METRIC|IMPERIAL)$")

    @field_validator("username")
    @classmethod
    def _no_reserved_username(cls, v: str) -> str:
        return validate_username_not_reserved(v)


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
    phone: str | None = None
    role: str
    system_role: str = "FARM_OWNER"  # 플랫폼 권한 기준(백엔드 effective_system_role) — 관리자 UI 게이팅용
    org_id: str | None
    language: str
    farm_ids: list[str]
    farm_roles: dict[str, str] = {}  # farm_id → 농장별 유효 role (멀티팜 게이팅용)


class MeUpdate(BaseModel):
    """프로필 자기수정(이름/연락처). 권한·role은 변경 불가."""
    name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=30)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class AccountDeleteRequest(BaseModel):
    """계정 삭제 요청 — 비밀번호 재확인 필수.

    되돌릴 수 없고 농장까지 비활성화하는 동작이라 방치된 세션·탈취 토큰만으로
    실행되면 안 된다(대표 결정 2026-08-25). GitHub·Google 도 동일하게 재인증을 요구한다.
    """

    password: str = Field(..., min_length=1, description="현재 비밀번호(재인증)")
