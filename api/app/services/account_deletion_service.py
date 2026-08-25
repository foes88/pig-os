"""계정 삭제(탈퇴) — Apple Guideline 5.1.1(v) 대응.

앱 안에서 계정을 만들 수 있으면 앱 안에서 삭제도 가능해야 한다. 고객센터 문의 방식은
인정되지 않는다. iOS 1.0 심사가 이 엔드포인트 하나로 막혀 있었다.

## 왜 행 삭제가 아니라 익명화인가 (대표 결정 2026-08-25)

`users` 행을 DELETE 하면 `period_locks.locked_by` 가 **NOT NULL + FK** 라 월마감 잠금
기록을 함께 지워야 한다. 그러면 **확정된 회계 기간이 조용히 풀린다** — 탈퇴 처리가
마감 데이터를 훼손하는 셈이다. 동의 이력(consent_ledger)도 사라져 "언제 동의하고
언제 철회했는지"를 증명할 수 없게 되는데, 그건 처리방침 제9조가 보관하도록 정한 항목이다.

그래서 **개인을 식별하는 값을 파기**하고 행 자체는 남긴다. 결과적으로:
  - 로그인 불가 (자격증명·토큰·기기 전부 제거)
  - 개인식별정보 없음 (이메일·아이디·이름·연락처 파기)
  - 같은 이메일로 재가입 가능 (unique 제약이 풀린다)
  - 마감 무결성·법정보존 항목 유지

PIPA 제21조의 "지체 없이 파기"는 **개인정보**를 대상으로 하며, 식별성을 제거하면
그 요구를 충족한다. 처리방침 제9조가 이미 이 구조(법정보존·동의증빙 예외)를 규정한다.

## 농장 데이터는 왜 지우지 않는가

농장 원천 데이터는 **가축 생산기록**이지 탈퇴자의 개인정보가 아니다. 계정 삭제를 이유로
되돌릴 수 없게 파기할 근거가 없다. 소유 농장은 `farms.active = false` 로 비활성화한다
(대표 결정: "구분값만 바꾸면 안 되나"). 비활성 농장은 배치 잡·목록에서 이미 빠진다.

다른 구성원이 남아 있는 농장은 **건드리지 않는다** — 타인의 데이터다. 멤버십만 해제한다.
"""
from __future__ import annotations

import asyncio
import uuid as _uuid
from dataclasses import dataclass, field

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, ValidationError
from app.core.security import verify_password
from app.db.models.ops import Device, Notification
from app.db.models.platform import (
    AuditLog,
    Farm,
    PasswordResetToken,
    RefreshToken,
    SyncQueue,
    User,
    UserFarm,
)

# 농장 소유로 보는 역할 — 이 역할만 남은 농장을 비활성화 대상으로 삼는다.
_OWNER_ROLES = ("FARM_OWNER", "OWNER")

# 파기 후 채워 넣는 자리표시값. unique NOT NULL 컬럼이라 NULL 로 둘 수 없다.
_ANON_EMAIL = "deleted-{k}@deleted.invalid"
_ANON_USERNAME = "deleted_{k}"
_ANON_NAME = "(deleted user)"


@dataclass
class DeletionResult:
    """무엇을 했는지 — 감사로그와 응답 근거로 쓴다."""

    user_id: str
    deactivated_farms: list[str] = field(default_factory=list)
    released_memberships: int = 0
    purged: dict[str, int] = field(default_factory=dict)


async def _owned_farms_to_deactivate(db: AsyncSession, user: User) -> tuple[list[Farm], list[str]]:
    """(비활성화할 농장, 다른 구성원이 있어 손대지 않는 농장 이름).

    ★ "소유"의 정의: organizations 에 owner 컬럼이 없으므로 user_farms 의 역할로 본다.
      role_override 가 비어 있으면 사용자 기본 role 을 따른다(권한 해석과 동일 규칙).
    """
    rows = (await db.execute(
        select(UserFarm.farm_id, UserFarm.role_override).where(UserFarm.user_id == user.id)
    )).all()
    owned_ids = [fid for fid, ovr in rows if (ovr or user.role) in _OWNER_ROLES]
    if not owned_ids:
        return [], []

    # 각 농장의 **다른** 구성원 수 — 남아 있으면 그 농장은 타인의 것이기도 하다.
    others = dict((await db.execute(
        select(UserFarm.farm_id, func.count())
        .where(UserFarm.farm_id.in_(owned_ids), UserFarm.user_id != user.id)
        .group_by(UserFarm.farm_id)
    )).all())

    solo_ids = [fid for fid in owned_ids if others.get(fid, 0) == 0]
    shared_ids = [fid for fid in owned_ids if others.get(fid, 0) > 0]

    farms = list((await db.scalars(select(Farm).where(Farm.id.in_(solo_ids)))).all()) if solo_ids else []
    shared_names = [
        n for n in (await db.scalars(select(Farm.name).where(Farm.id.in_(shared_ids)))).all()
    ] if shared_ids else []
    return farms, shared_names


async def delete_account(db: AsyncSession, user: User, password: str) -> DeletionResult:
    """계정 삭제. 되돌릴 수 없다.

    비밀번호 재확인을 요구한다 — 방치된 세션이나 탈취 토큰으로 실행되면 안 되는
    동작이다(대표 결정 2026-08-25). GitHub·Google 도 같은 방식이다.
    """
    if not password:
        raise ValidationError("password is required to delete the account")
    # bcrypt 는 CPU 바운드 — 이벤트 루프를 막지 않도록 스레드로 넘긴다(로그인과 동일).
    if not await asyncio.to_thread(verify_password, password, user.password_hash):
        raise ForbiddenError("password does not match")

    farms_to_deactivate, shared_names = await _owned_farms_to_deactivate(db, user)

    result = DeletionResult(user_id=str(user.id))
    # 다른 구성원이 있는 농장은 남긴다 — 멤버십만 해제된다. 응답에 알려 준다.
    result.purged["shared_farms_kept"] = len(shared_names)

    for farm in farms_to_deactivate:
        farm.active = False
        result.deactivated_farms.append(str(farm.id))

    # ── 개인 소유 부수 데이터 제거 ────────────────────────────────────────
    # 이건 전부 "그 사람의 것"이라 남길 이유가 없다. 세션·기기·알림·미동기화 큐.
    for model, key in (
        (RefreshToken, "user_id"),
        (PasswordResetToken, "user_id"),
        (Device, "user_id"),
        (Notification, "user_id"),
        (SyncQueue, "user_id"),
    ):
        r = await db.execute(delete(model).where(getattr(model, key) == user.id))
        result.purged[model.__tablename__] = r.rowcount or 0

    r = await db.execute(delete(UserFarm).where(UserFarm.user_id == user.id))
    result.released_memberships = r.rowcount or 0

    # ── 감사 흔적에서 개인 연결 끊기 ─────────────────────────────────────
    # audit_log.user_id 는 nullable 이다. 행은 남기고 사람만 지운다 — 어떤 변경이
    # 있었는지는 운영·법정 대응에 필요하지만 누구였는지는 파기 대상이다.
    r = await db.execute(
        update(AuditLog).where(AuditLog.user_id == user.id).values(user_id=None)
    )
    result.purged["audit_log_unlinked"] = r.rowcount or 0

    # ── 식별정보 파기 ────────────────────────────────────────────────────
    # ★ 행을 지우지 않는 이유는 모듈 docstring 참조(period_locks 무결성·동의 증빙).
    k = _uuid.uuid4().hex[:12]
    user.email = _ANON_EMAIL.format(k=k)
    user.username = _ANON_USERNAME.format(k=k)
    user.name = _ANON_NAME
    user.phone = None
    # 로그인 불가능한 해시로 교체 — 빈 문자열은 verify 가 예외를 낼 수 있어 난수를 넣는다.
    user.password_hash = "!deleted!" + _uuid.uuid4().hex
    user.active = False
    user.org_id = None

    await db.flush()
    return result
