"""농장 멤버(구성원) 스키마 — /settings/users.

멤버 = UserFarm로 농장에 연결된 사용자. 역할은 farm 레벨 override(없으면 org role).
이메일 발송 불가 환경이므로 '초대'는 관리자가 계정+초기 비밀번호를 생성하는 방식.
"""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

_FARM_ROLES = "^(FARM_OWNER|FARM_MANAGER|FARM_WORKER|VET|VIEWER)$"


class MemberResponse(BaseModel):
    user_id: UUID
    name: str
    email: str | None
    role: str          # 농장 레벨 유효 역할 (role_override or user.role)
    active: bool


class MemberCreate(BaseModel):
    # ACC-C-hardening: 알 수 없는 필드(system_role/approval_status 등) 주입 차단(방어심층).
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., pattern=r"^[a-zA-Z0-9_.-]{3,50}$", description="직원 로그인 아이디")
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(default="FARM_WORKER", pattern=_FARM_ROLES)


class MemberUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str | None = Field(default=None, pattern=_FARM_ROLES)
    active: bool | None = None
