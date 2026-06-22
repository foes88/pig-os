"""운영자 어드민 — 회원/베타가입 스키마 (PigOS 네이티브).

레거시 officers VO 복제 아님. PigOS User/UserFarm/PilotSignup 모델 기반.
"""
from pydantic import BaseModel

APPROVAL_STATUSES = {"PENDING", "APPROVED", "REJECTED"}


class AdminMemberRow(BaseModel):
    id: str
    email: str | None
    name: str
    role: str
    system_role: str
    approval_status: str
    active: bool
    org_id: str | None
    org_name: str | None
    farm_count: int
    created_at: str | None
    last_login_at: str | None


class AdminMemberFarm(BaseModel):
    farm_id: str
    role: str


class AdminMemberDetail(AdminMemberRow):
    farms: list[AdminMemberFarm]


class MemberStatusUpdate(BaseModel):
    approval_status: str | None = None
    active: bool | None = None


# ── 베타(파일럿) 가입 ──────────────────────────────────────────────────────────
class PilotSignupRow(BaseModel):
    id: str
    name: str
    email: str
    farm_size: str
    country: str
    role: str
    lang: str
    status: str
    notes: str | None
    created_at: str | None


class PilotApproveRequest(BaseModel):
    """승인 시 운영 계정 생성(이메일 발송 불가 → 초기 비밀번호 직접 발급)."""
    initial_password: str
    system_role: str = "FARM_OWNER"


class PilotApproveResult(BaseModel):
    user_id: str
    email: str
    initial_password: str
    note: str
