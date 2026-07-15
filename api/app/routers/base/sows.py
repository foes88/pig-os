from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import CurrentUser, DbDep, FarmDep, require_farm_role
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.models.events import (
    Farrowing,
    Mating,
    PigletEvent,
    PregnancyCheck,
    ReproductiveEvent,
    Weaning,
)
from app.db.models.health import HealthEvent, Removal
from app.db.models.platform import AuditLog
from app.db.models.sow import PigletTransfer, Sow
from app.schemas.common import PagedResponse, PageMeta
from app.schemas.events import PigletEventCreate, WeaningCreate
from app.schemas.sow import (
    RemovalResponse,
    SowCreate,
    SowCullRequest,
    SowResponse,
    SowUpdate,
)
from app.services.event_service import (
    _ensure_period_unlocked,
    _get_open_cycle,
    count_unweaned_piglets,
    record_piglet_event,
    record_weaning,
)

router = APIRouter(prefix="/farms/{farm_id}/sows", tags=["Sows"])

# 파괴적 작업(도태·삭제)은 농장 OWNER/MANAGER만 (Section D RBAC)
_MANAGE_ROLES = ("FARM_OWNER", "FARM_MANAGER", "SUPER_ADMIN", "VENDOR_ADMIN", "DISTRIBUTOR_ADMIN", "DEALER_ADMIN")
# 일상 입력/수정 = WORKER 이상 (VIEWER/VET/API_CLIENT 읽기전용 차단) — Section D2
_ENTRY_ROLES = ("FARM_OWNER", "FARM_MANAGER", "FARM_WORKER", "SUPER_ADMIN", "VENDOR_ADMIN", "DISTRIBUTOR_ADMIN", "DEALER_ADMIN")


@router.get("", response_model=PagedResponse[SowResponse])
async def list_sows(
    farm: FarmDep,
    db: DbDep,
    status: str | None = Query(
        None,
        pattern="^(GILT|OPEN|PREGNANT|LACTATING|ACCIDENT|CULLED|DEAD|SOLD|TRANSFER)$",
        description="SowStatus v2. 잘못된 값은 422 (빈 목록 조용히 반환 방지)",
    ),
    building_id: UUID | None = Query(None),
    parity_min: int | None = Query(None, ge=0),
    parity_max: int | None = Query(None, le=20),
    search: str | None = Query(None, description="ear_tag 부분일치 검색"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200, alias="per_page"),
):
    q = select(Sow).where(Sow.farm_id == farm.id, Sow.deleted_at.is_(None))
    if status:
        q = q.where(Sow.status == status)
    if building_id:
        q = q.where(Sow.building_id == building_id)
    if parity_min is not None:
        q = q.where(Sow.parity >= parity_min)
    if parity_max is not None:
        q = q.where(Sow.parity <= parity_max)
    if search and search.strip():
        q = q.where(Sow.ear_tag.ilike(f"%{search.strip()}%"))

    from sqlalchemy import func
    count_row = await db.scalar(select(func.count()).select_from(q.subquery()))
    total = count_row or 0
    pages = max(1, (total + per_page - 1) // per_page)

    q = q.order_by(Sow.ear_tag).offset((page - 1) * per_page).limit(per_page)
    rows = await db.scalars(q)
    sows = list(rows)

    return PagedResponse(
        items=[SowResponse.model_validate(s) for s in sows],
        meta=PageMeta(
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        ),
    )


@router.post("", response_model=SowResponse, status_code=201,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def create_sow(body: SowCreate, farm: FarmDep, db: DbDep, current_user: CurrentUser):  # noqa: E501
    # V4 정합성: 입식일 미래 금지 + 활성 귀표 중복 차단(깨끗한 422; DB unique는 500이라 사전 검사)
    # 서버 UTC vs 앞선 타임존(최대 UTC+14) 사용자 → 로컬 '오늘'이 UTC 날짜보다 하루 앞설 수 있음.
    # +1일 유예로 타임존 스큐 허용(진짜 미래=내일+ 는 여전히 차단). 이상적으론 farm.timezone 기준.
    if body.entry_date > datetime.now(UTC).date() + timedelta(days=1):
        raise ValidationError("entry_date cannot be in the future")
    dup = await db.scalar(
        select(Sow).where(
            Sow.farm_id == farm.id, Sow.ear_tag == body.ear_tag, Sow.deleted_at.is_(None)
        )
    )
    if dup:
        # 중복 이표 = 충돌(409). 사전검사·동시race(아래 IntegrityError) 모두 409로 일관 —
        # 모바일 계약(중복 이표 전용 처리) 및 matings 동일날짜 중복(409)과 정합.
        raise ConflictError(f"ear_tag '{body.ear_tag}' already exists in this farm")

    sow = Sow(
        farm_id=farm.id,
        ear_tag=body.ear_tag,
        rfid_tag=body.rfid_tag,
        entry_date=datetime.combine(body.entry_date, datetime.min.time()).replace(tzinfo=UTC),  # noqa: E501
        entry_type=body.entry_type,
        breed=body.breed,
        breed_company=body.breed_company,
        building_id=body.building_id,
        parity=body.parity,
        source_farm_id=body.source_farm_id,
        # 미경산(parity=0) → 후보돈, 경산돈 전입 → 공태로 입식
        status="GILT" if (body.parity or 0) == 0 else "OPEN",
    )
    db.add(sow)
    try:
        await db.commit()
    except IntegrityError:
        # 동시 생성 TOCTOU: dup-check 통과 후 두 요청이 같은 ear_tag INSERT → UNIQUE(farm_id,ear_tag)
        # 위반. 피그플랜 MAX+1 채번 경쟁조건의 PigOS 대응 — 500 대신 깔끔한 409(ConflictError).
        await db.rollback()
        raise ConflictError(f"ear_tag '{body.ear_tag}' already exists in this farm")
    await db.refresh(sow)
    return SowResponse.model_validate(sow)


# ★ 정적 경로 /removals 는 동적 /{sow_id} 보다 먼저 등록해야 함(아니면 "removals"를
#   sow_id로 파싱해 uuid_parsing 422 — B7 도폐사이력 화면 불능 근인. 2026-06-24 수정).
@router.get("/removals", response_model=list[RemovalResponse])
async def list_removals(
    farm: FarmDep,
    db: DbDep,
    removal_type: str | None = Query(None, description="CULLED|DEAD|SOLD|TRANSFER"),
    limit: int = Query(50, ge=1, le=200),
):
    """도폐사·판매 이력 목록."""
    q = select(Removal).where(Removal.farm_id == farm.id)
    if removal_type:
        q = q.where(Removal.removal_type == removal_type)
    q = q.order_by(Removal.removal_date.desc()).limit(limit)
    rows = await db.scalars(q)
    return [RemovalResponse.model_validate(r) for r in rows]


@router.get("/{sow_id}", response_model=SowResponse)
async def get_sow(sow_id: UUID, farm: FarmDep, db: DbDep):
    sow = await db.scalar(
        select(Sow).where(Sow.id == sow_id, Sow.farm_id == farm.id, Sow.deleted_at.is_(None))  # noqa: E501
    )
    if not sow:
        raise NotFoundError(f"Sow {sow_id} not found")
    return SowResponse.model_validate(sow)


@router.patch("/{sow_id}", response_model=SowResponse,
              dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def update_sow(sow_id: UUID, body: SowUpdate, farm: FarmDep, db: DbDep):
    sow = await db.scalar(
        select(Sow).where(Sow.id == sow_id, Sow.farm_id == farm.id, Sow.deleted_at.is_(None))  # noqa: E501
    )
    if not sow:
        raise NotFoundError(f"Sow {sow_id} not found")
    updated = body.model_dump(exclude_none=True)
    # 상태전이 가드: LACTATING/PREGNANT는 분만/교배 이벤트로만 도달 가능(분만 없는 포유·
    # 교배 없는 임신 같은 물리 불가 상태를 PATCH로 만드는 것 차단). OPEN/GILT/ACCIDENT는
    # 미기록 이벤트를 함의하지 않아 수동 보정 허용. (이벤트-구동 상태머신의 PATCH 우회 방지)
    if updated.get("status") in ("LACTATING", "PREGNANT") and updated["status"] != sow.status:
        raise ValidationError(
            f"status '{updated['status']}' is set by mating/farrowing events, "
            f"not by direct edit (record the event instead)")
    # ear_tag 변경 시 유니크 재검증(create_sow와 동일) — 미검증 시 활성 중복이표 또는 500 누설(QA 모돈 update 패리티).
    if "ear_tag" in updated and updated["ear_tag"] != sow.ear_tag:
        dup = await db.scalar(select(Sow).where(
            Sow.farm_id == farm.id, Sow.ear_tag == updated["ear_tag"],
            Sow.deleted_at.is_(None), Sow.id != sow.id))
        if dup:
            raise ValidationError(f"ear_tag '{updated['ear_tag']}' already exists in this farm")
    for k, v in updated.items():
        setattr(sow, k, v)
    await db.commit()
    await db.refresh(sow)
    return SowResponse.model_validate(sow)


@router.post("/{sow_id}/cull", response_model=RemovalResponse, status_code=201,
             dependencies=[require_farm_role(*_MANAGE_ROLES)])
async def cull_sow(
    sow_id: UUID,
    body: SowCullRequest,
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
):
    """
    ?꾪룓???먮ℓ/?꾩텧 泥섎━.
    - 紐⑤룉 ?곹깭瑜?removal_type?쇰줈 ?꾪솚 + soft-delete
    - removals ?대젰 ?뚯씠釉붿뿉 ?곸꽭 湲곕줉
    - audit_log 湲곕줉
    """
    sow = await db.scalar(
        select(Sow).where(Sow.id == sow_id, Sow.farm_id == farm.id, Sow.deleted_at.is_(None))  # noqa: E501
    )
    if not sow:
        raise NotFoundError(f"Sow {sow_id} not found")

    # 정합성: 도폐사일은 입식일 이후 & 미래일 금지 (입적 이력 보호)
    entry_d = sow.entry_date.date() if hasattr(sow.entry_date, "date") else sow.entry_date
    if entry_d and body.removal_date < entry_d:
        raise ValidationError("removal_date cannot be before the sow's entry_date")
    if body.removal_date > datetime.now(UTC).date() + timedelta(days=1):
        raise ValidationError("removal_date cannot be in the future")

    # 월마감 잠금: 도폐사일이 속한 월이 잠겨있으면 423 (확정 데이터 보호 — 다른 이벤트 경로와 동일).
    # removal은 모돈 수/PSY 분모·손실·일별보고서 입력이라 잠긴 월로 백데이트 금지.
    await _ensure_period_unlocked(db, farm.id, body.removal_date)

    # Rule ② (docs/specs/2026-07-10_lactating-cull-piglet-rule.md): 포유중 모돈을 도태/판매/전출할 때
    # 잔여(미이유) 자돈이 고아가 되지 않도록 처리방식을 명시 강제. 잔여>0인데 미지정 → 422.
    # FOSTER_TO(대상모돈 전출)·DEATH(자돈 폐사 명시)·WEAN(조기 이유) 중 택일 실행 후 도태.
    # (DEAD 사고사는 현실상 차단 불가 → 강제 안 함. 잔여 0이면 처리 불필요.)
    if sow.status == "LACTATING" and body.removal_type in ("CULLED", "SOLD", "TRANSFER"):
        remaining, farrowing = await count_unweaned_piglets(db, farm.id, sow.id)
        if remaining > 0:
            disp = body.piglet_disposition
            fid = farrowing.id if farrowing else None
            if disp is None:
                raise ValidationError(
                    f"Sow is lactating with {remaining} un-weaned piglet(s) — set "
                    "piglet_disposition (FOSTER_TO / DEATH / WEAN)"
                )
            if disp == "FOSTER_TO":
                if not body.foster_target_sow_id:
                    raise ValidationError("FOSTER_TO requires foster_target_sow_id")
                await record_piglet_event(db, farm.id, current_user.id, PigletEventCreate(
                    sow_id=sow.id, farrowing_id=fid, event_date=body.removal_date,
                    event_type="FOSTER_OUT", piglet_count=remaining,
                    target_sow_id=body.foster_target_sow_id))
            elif disp == "DEATH":
                await record_piglet_event(db, farm.id, current_user.id, PigletEventCreate(
                    sow_id=sow.id, farrowing_id=fid, event_date=body.removal_date,
                    event_type="DEATH", piglet_count=remaining,
                    reason=body.piglet_death_reason or "OTHER"))
            elif disp == "WEAN":
                await record_weaning(db, farm.id, current_user.id, WeaningCreate(
                    sow_id=sow.id, farrowing_id=fid, weaning_date=body.removal_date,
                    weaned_count=remaining), import_mode=True)
            # 처리 서비스가 내부 커밋 → sow 재조회(스테일 객체 방지). 중간상태도 유효(재시도 수렴).
            sow = await db.scalar(select(Sow).where(
                Sow.id == sow_id, Sow.farm_id == farm.id, Sow.deleted_at.is_(None)))
            if not sow:
                raise NotFoundError(f"Sow {sow_id} not found")

    now = datetime.now(UTC)

    # 紐⑤룉 ?곹깭 + soft-delete
    sow.status = body.removal_type
    sow.exit_date = now
    sow.deleted_at = now

    # F5: 진행 중이던 번식 사이클 종료(FAILED). 미종료 시 모돈 제거 후에도 사이클이
    # 영구 open으로 남아 open-cycle·번식 분석 오염(apply_terminal_reproductive와 동일).
    open_cycle = await _get_open_cycle(db, sow.id)
    if open_cycle:
        open_cycle.cycle_status = "FAILED"
        open_cycle.ended_at = now

    # removals ?대젰
    removal = Removal(
        farm_id=farm.id,
        sow_id=sow.id,
        removal_date=body.removal_date,
        removal_type=body.removal_type,
        reason_category=body.reason_category,
        reason_detail=body.reason_detail,
        body_weight_kg=body.body_weight_kg,
        sale_price=body.sale_price,
        sale_currency=body.sale_currency,
        created_by=current_user.id,
    )
    db.add(removal)

    # audit log
    db.add(AuditLog(
        user_id=current_user.id,
        farm_id=farm.id,
        action="CULL",
        entity_type="sows",
        entity_id=sow.id,
        new_value=body.model_dump(mode="json"),
    ))

    await db.commit()
    await db.refresh(removal)
    return RemovalResponse.model_validate(removal)


@router.delete("/{sow_id}", status_code=204,
               dependencies=[require_farm_role(*_MANAGE_ROLES)])
async def delete_sow(sow_id: UUID, farm: FarmDep, db: DbDep):
    sow = await db.scalar(
        select(Sow).where(Sow.id == sow_id, Sow.farm_id == farm.id, Sow.deleted_at.is_(None))  # noqa: E501
    )
    if not sow:
        raise NotFoundError(f"Sow {sow_id} not found")
    now = datetime.now(UTC)
    sow.deleted_at = now
    # 캐스케이드 soft-delete — 삭제 모돈의 번식 이벤트가 events 조회·보고서에 dangling 잔존하면
    # born_alive_sum 등 수치가 오염된다(QA ws_crud_delete 발견). 모돈 삭제 = 그 이벤트도 제거.
    # PigletEvent(양자/폐사)·PregnancyCheck·HealthEvent도 포함 — 누락 시 _calc_piglet_adjustments가
    # 고아 양자이벤트를 읽어 양자상대 모돈의 effective litter/nursing 분모가 오염된다(QA B1 두수보존).
    for Model in (Mating, Farrowing, Weaning, ReproductiveEvent,
                  PigletEvent, PregnancyCheck, HealthEvent):
        await db.execute(
            update(Model)
            .where(Model.sow_id == sow_id, Model.deleted_at.is_(None))
            .values(deleted_at=now)
        )
    # QA #4 (MIGRATION-PENDING a1c3e5b7d9f2): PigletTransfer는 source/dest_sow_id 참조 → 별도 캐스케이드.
    await db.execute(
        update(PigletTransfer)
        .where((PigletTransfer.source_sow_id == sow_id) | (PigletTransfer.dest_sow_id == sow_id),
               PigletTransfer.deleted_at.is_(None))
        .values(deleted_at=now)
    )
    await db.commit()
