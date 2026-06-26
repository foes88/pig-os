"""운영자 어드민 — 회원/가입승인 (Phase 1, PigOS 네이티브).

전사 사용자 조회·검색·상태변경 + 베타(파일럿) 가입 승인(운영 계정 생성).
모든 라우트 require_super_admin. 상태변경은 AuditLog 기록.
레거시 officers/UserInfo.do 복제 아님 — PigOS User/UserFarm/PilotSignup 기반.
"""
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select

from app.core.dependencies import DbDep, SuperAdmin, require_super_admin
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.security import hash_password
from app.db.models.pilot_signup import PilotSignup
from app.db.models.platform import AuditLog, Farm, Organization, User, UserFarm
from app.schemas.admin_user import (
    APPROVAL_STATUSES,
    AdminMemberDetail,
    AdminMemberFarm,
    AdminMemberRow,
    MemberStatusUpdate,
    PilotApproveRequest,
    PilotApproveResult,
    PilotSignupRow,
)
from app.schemas.common import PagedResponse, PageMeta
from app.services.farm_service import _generate_farm_code

router = APIRouter(
    prefix="/admin",
    tags=["Admin · Users"],
    dependencies=[Depends(require_super_admin)],
)

_SYSTEM_ROLES = {"SUPER_ADMIN", "VENDOR_ADMIN", "DISTRIBUTOR_ADMIN", "DEALER_ADMIN",
                 "FARM_OWNER", "FARM_MANAGER", "FARM_WORKER", "VET", "VIEWER"}


def _row_to_member(u: User, org_name: str | None, farm_count: int) -> AdminMemberRow:
    return AdminMemberRow(
        id=str(u.id),
        email=u.email,
        name=u.name,
        role=u.role,
        system_role=u.system_role,
        approval_status=u.approval_status,
        active=u.active,
        org_id=str(u.org_id) if u.org_id else None,
        org_name=org_name,
        farm_count=farm_count,
        created_at=u.created_at.isoformat() if u.created_at else None,
        last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
    )


# ─── 회원 ─────────────────────────────────────────────────────────────────────
@router.get("/members", response_model=PagedResponse[AdminMemberRow])
async def list_members(
    db: DbDep,
    _admin: SuperAdmin,
    q: Annotated[str | None, Query(description="이메일/이름 부분검색")] = None,
    status: Annotated[str | None, Query(description="승인상태(PENDING/APPROVED/REJECTED)")] = None,
    org_id: Annotated[UUID | None, Query(description="조직 필터")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PagedResponse[AdminMemberRow]:
    """전사 회원 목록 — 검색·상태/조직 필터·페이지네이션."""
    conds = []
    if q:
        like = f"%{q.strip()}%"
        conds.append(or_(User.email.ilike(like), User.name.ilike(like)))
    if status:
        st = status.upper()
        if st not in APPROVAL_STATUSES:
            raise ValidationError(f"Invalid status. Allowed: {', '.join(sorted(APPROVAL_STATUSES))}")
        conds.append(User.approval_status == st)
    if org_id:
        conds.append(User.org_id == org_id)

    total = await db.scalar(select(func.count()).select_from(User).where(*conds)) or 0
    pages = max(1, (total + per_page - 1) // per_page)

    rows = (
        await db.execute(
            select(User, Organization.name)
            .outerjoin(Organization, Organization.id == User.org_id)
            .where(*conds)
            .order_by(User.created_at.desc())
            .limit(per_page)
            .offset((page - 1) * per_page)
        )
    ).all()

    user_ids = [u.id for (u, _) in rows]
    fc: dict[UUID, int] = {}
    if user_ids:
        for uid, cnt in (
            await db.execute(
                select(UserFarm.user_id, func.count())
                .where(UserFarm.user_id.in_(user_ids))
                .group_by(UserFarm.user_id)
            )
        ).all():
            fc[uid] = cnt

    items = [_row_to_member(u, org_name, fc.get(u.id, 0)) for (u, org_name) in rows]
    return PagedResponse(items=items, meta=PageMeta(total=total, page=page, per_page=per_page, pages=pages))


@router.get("/members/{member_id}", response_model=AdminMemberDetail)
async def get_member(member_id: UUID, db: DbDep, _admin: SuperAdmin) -> AdminMemberDetail:
    """회원 상세 — 소속 농장/역할 포함."""
    row = (
        await db.execute(
            select(User, Organization.name)
            .outerjoin(Organization, Organization.id == User.org_id)
            .where(User.id == member_id)
        )
    ).first()
    if not row:
        raise NotFoundError("Member not found")
    u, org_name = row

    farm_rows = (
        await db.execute(
            select(UserFarm.farm_id, UserFarm.role_override).where(UserFarm.user_id == member_id)
        )
    ).all()
    farms = [AdminMemberFarm(farm_id=str(fid), role=role or u.role) for (fid, role) in farm_rows]

    base = _row_to_member(u, org_name, len(farms))
    return AdminMemberDetail(**base.model_dump(), farms=farms)


@router.patch("/members/{member_id}/status", response_model=AdminMemberRow)
async def update_member_status(
    member_id: UUID, body: MemberStatusUpdate, db: DbDep, admin: SuperAdmin
) -> AdminMemberRow:
    """가입 승인/반려 + 활성 토글. 변경 전/후를 AuditLog에 기록."""
    u = await db.get(User, member_id)
    if not u:
        raise NotFoundError("Member not found")

    before: dict = {}
    after: dict = {}
    if body.approval_status is not None:
        st = body.approval_status.upper()
        if st not in APPROVAL_STATUSES:
            raise ValidationError(f"Invalid status. Allowed: {', '.join(sorted(APPROVAL_STATUSES))}")
        before["approval_status"] = u.approval_status
        after["approval_status"] = st
        u.approval_status = st
    if body.active is not None:
        before["active"] = u.active
        after["active"] = body.active
        u.active = body.active

    if after:
        db.add(
            AuditLog(
                user_id=admin.id,
                farm_id=None,
                action="UPDATE",
                entity_type="admin_user",
                entity_id=u.id,
                old_value=before,
                new_value=after,
            )
        )
    await db.commit()
    await db.refresh(u)

    fc = await db.scalar(select(func.count()).select_from(UserFarm).where(UserFarm.user_id == u.id)) or 0
    org_name = await db.scalar(select(Organization.name).where(Organization.id == u.org_id)) if u.org_id else None
    return _row_to_member(u, org_name, fc)


# ─── 베타(파일럿) 가입 ──────────────────────────────────────────────────────────
@router.get("/pilot-signups", response_model=PagedResponse[PilotSignupRow])
async def list_pilot_signups(
    db: DbDep,
    _admin: SuperAdmin,
    status: Annotated[str | None, Query(description="pending/contacted/onboarded/rejected")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PagedResponse[PilotSignupRow]:
    """베타 가입 접수 목록."""
    conds = []
    if status:
        conds.append(PilotSignup.status == status.lower())
    total = await db.scalar(select(func.count()).select_from(PilotSignup).where(*conds)) or 0
    pages = max(1, (total + per_page - 1) // per_page)
    rows = (
        await db.execute(
            select(PilotSignup).where(*conds)
            .order_by(PilotSignup.created_at.desc())
            .limit(per_page).offset((page - 1) * per_page)
        )
    ).scalars().all()
    items = [
        PilotSignupRow(
            id=str(p.id), name=p.name, email=p.email, farm_size=p.farm_size,
            country=p.country, role=p.role, lang=p.lang, status=p.status,
            notes=p.notes, created_at=p.created_at.isoformat() if p.created_at else None,
        )
        for p in rows
    ]
    return PagedResponse(items=items, meta=PageMeta(total=total, page=page, per_page=per_page, pages=pages))


@router.post("/pilot-signups/{signup_id}/approve", response_model=PilotApproveResult)
async def approve_pilot_signup(
    signup_id: UUID, body: PilotApproveRequest, db: DbDep, admin: SuperAdmin
) -> PilotApproveResult:
    """베타 가입 승인 → 운영 계정(Org+User+Farm+UserFarm) 생성.

    이메일 발송 불가 환경 → 초기 비밀번호를 운영자가 발급해 직접 전달.
    """
    p = await db.get(PilotSignup, signup_id)
    if not p:
        raise NotFoundError("Signup not found")
    if p.status == "onboarded":
        raise ConflictError("Already onboarded")
    if len(body.initial_password) < 8:
        raise ValidationError("initial_password must be at least 8 characters")
    if body.system_role not in _SYSTEM_ROLES:
        raise ValidationError(f"Invalid system_role. Allowed: {', '.join(sorted(_SYSTEM_ROLES))}")

    existing = await db.scalar(select(User).where(User.email == p.email))
    if existing:
        raise ConflictError(f"User already exists for {p.email}")

    # username = email 로컬파트(충돌 시 id 접미). 파일럿 승인은 저볼륨.
    base_username = (p.email.split("@")[0] or "user")[:40]
    username = base_username
    if await db.scalar(select(User).where(User.username == username)):
        username = f"{base_username}_{uuid4().hex[:8]}"

    # Org/Farm.country 는 2자 국가코드 → 가입 자유텍스트(예: "Vietnam")에서 앞 2자 코드화
    country_code = (p.country or "XX")[:2].upper()
    org = Organization(name=f"{p.name} Org", country=country_code, timezone="UTC")
    db.add(org)
    await db.flush()

    user = User(
        org_id=org.id,
        username=username,
        email=p.email,
        name=p.name,
        password_hash=hash_password(body.initial_password),
        role="FARM_OWNER",
        system_role=body.system_role,
        language=p.lang,
        approval_status="APPROVED",
    )
    db.add(user)
    await db.flush()

    farm = Farm(
        org_id=org.id,
        farm_code=_generate_farm_code(country_code, org.id),
        name=f"{p.name} Farm",
        country=country_code,
        timezone="UTC",
    )
    db.add(farm)
    await db.flush()
    db.add(UserFarm(user_id=user.id, farm_id=farm.id, role_override="FARM_OWNER"))

    p.status = "onboarded"
    db.add(
        AuditLog(
            user_id=admin.id, farm_id=farm.id, action="CREATE",
            entity_type="pilot_approval", entity_id=user.id,
            old_value={"signup_status": "pending"},
            new_value={"signup_status": "onboarded", "user_id": str(user.id)},
        )
    )
    await db.commit()

    return PilotApproveResult(
        user_id=str(user.id),
        email=p.email,
        initial_password=body.initial_password,
        note="운영 계정 생성 완료. 초기 비밀번호를 가입자에게 직접 전달하세요(이메일 발송 불가).",
    )
