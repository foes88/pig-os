"""
농장 구성원 관리 — /api/v1/farms/{farm_id}/members  (설정 > 사용자)

멤버 = UserFarm로 농장에 연결된 사용자. 역할은 farm 레벨 role_override 우선.
이메일 발송 불가 환경 → '초대'는 관리자가 계정+초기 비밀번호 생성으로 처리.
관리(생성/수정)는 FARM_OWNER(소유자) 전용. MANAGER는 일상 운영만, 멤버 임명 불가.
"""
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbDep, FarmDep, require_farm_role
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.db.models.platform import AuditLog, User, UserFarm
from app.schemas.member import MemberCreate, MemberResponse, MemberUpdate

router = APIRouter(prefix="/farms", tags=["Members"])

# 멤버 관리(생성/수정)는 소유자 전용 — 누가 농장에 접근하는지는 OWNER 권한.
# (MANAGER는 일상 운영은 가능하되 멤버 임명/역할변경은 불가.)
_OWNER_ROLES = ("FARM_OWNER", "SUPER_ADMIN")


def _to_response(user: User, link: UserFarm) -> MemberResponse:
    return MemberResponse(
        user_id=user.id,
        name=user.name,
        email=user.email,
        role=link.role_override or user.role,
        active=user.active,
    )


@router.get("/{farm_id}/members", response_model=list[MemberResponse])
async def list_members(farm: FarmDep, db: DbDep):
    rows = await db.execute(
        select(User, UserFarm)
        .join(UserFarm, UserFarm.user_id == User.id)
        .where(UserFarm.farm_id == farm.id)
        .order_by(User.name)
    )
    return [_to_response(u, link) for u, link in rows.all()]


@router.post(
    "/{farm_id}/members",
    response_model=MemberResponse,
    status_code=201,
    dependencies=[require_farm_role(*_OWNER_ROLES)],
)
async def create_member(
    body: MemberCreate, farm: FarmDep, db: DbDep, current_user: CurrentUser
):
    if await db.scalar(select(User).where(User.username == body.username)):
        raise ConflictError(f"Username '{body.username}' already taken")
    if await db.scalar(select(User).where(User.email == body.email)):
        raise ConflictError(f"User with email {body.email} already exists")

    user = User(
        org_id=farm.org_id,
        username=body.username,
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
        role=body.role,
        # 농장권한은 role_override(require_farm_role)로 판정하지만, system_role도 일관 유지
        # (조직레벨 접근/레거시 폴백용). 미설정 시 기본 FARM_OWNER가 되어 과권한 위험.
        system_role=body.role,
    )
    db.add(user)
    await db.flush()

    link = UserFarm(user_id=user.id, farm_id=farm.id, role_override=body.role)
    db.add(link)
    db.add(AuditLog(
        user_id=current_user.id,
        farm_id=farm.id,
        action="CREATE",
        entity_type="user_farms",
        entity_id=user.id,
        new_value={"email": body.email, "role": body.role},
    ))
    await db.commit()
    await db.refresh(user)
    return _to_response(user, link)


@router.patch(
    "/{farm_id}/members/{user_id}",
    response_model=MemberResponse,
    dependencies=[require_farm_role(*_OWNER_ROLES)],
)
async def update_member(
    user_id: UUID, body: MemberUpdate, farm: FarmDep, db: DbDep, current_user: CurrentUser
):
    link = await db.scalar(
        select(UserFarm).where(UserFarm.user_id == user_id, UserFarm.farm_id == farm.id)
    )
    if not link:
        raise NotFoundError(f"Member {user_id} not found in farm")
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")

    changed: dict = {}
    if body.role is not None:
        # 농장 멤버 역할은 farm-scoped role_override만 갱신(QA 보안리뷰 M2).
        # 전역 user.role/system_role를 덮어쓰면 멀티팜 유저의 타농장 유효권한(role_override NULL 폴백)이
        # 동반 변경되는 누출 → 제거. 응답은 _to_response가 role_override 우선 표시.
        link.role_override = body.role
        changed["role"] = body.role
    if body.active is not None:
        user.active = body.active
        changed["active"] = body.active

    db.add(AuditLog(
        user_id=current_user.id,
        farm_id=farm.id,
        action="UPDATE",
        entity_type="user_farms",
        entity_id=user.id,
        new_value=changed,
    ))
    await db.commit()
    await db.refresh(user)
    return _to_response(user, link)
