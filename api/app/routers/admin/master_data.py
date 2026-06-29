"""운영자 어드민 — 코드/마스터 데이터 CRUD (G4).

질병코드·백신·약품·이벤트정의를 관리자 콘솔에서 조회/생성/수정/삭제.
전 테이블 문자열 PK + 단순 컬럼이라 레지스트리 기반 제네릭 CRUD(테이블별 보일러플레이트 회피).
SUPER_ADMIN 전용, 모든 변경 AuditLog. 마스터 데이터는 카탈로그라 hard-delete(soft-delete 컬럼 없음).
"""
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Body, Depends
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError

from app.core.dependencies import DbDep, SuperAdmin, require_super_admin
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.models.master import (
    DiseaseCode,
    EventDefinition,
    MedicationCatalog,
    VaccineCatalog,
)
from app.db.models.platform import AuditLog

router = APIRouter(
    prefix="/admin/master",
    tags=["Admin · Master Data"],
    dependencies=[Depends(require_super_admin)],
)

# kind(URL) → (모델, PK 컬럼명). 새 코드테이블은 여기만 추가하면 CRUD 자동 제공.
_KINDS: dict[str, tuple[type, str]] = {
    "diseases": (DiseaseCode, "disease_code"),
    "vaccines": (VaccineCatalog, "vaccine_code"),
    "medications": (MedicationCatalog, "active_substance"),
    "event-definitions": (EventDefinition, "event_code"),
}


def _resolve(kind: str) -> tuple[type, str]:
    if kind not in _KINDS:
        raise NotFoundError(f"Unknown master-data kind. Allowed: {', '.join(sorted(_KINDS))}")
    return _KINDS[kind]


def _cols(model: type) -> set[str]:
    return {c.name for c in model.__table__.columns}


def _to_dict(model: type, row: object) -> dict:
    out: dict = {}
    for c in model.__table__.columns:
        v = getattr(row, c.name)
        out[c.name] = float(v) if isinstance(v, Decimal) else v
    return out


def _check_type(model: type, key: str, v: object) -> None:
    """컬럼 파이썬 타입과 값 타입 정합 검증(미검증 dict→타입오류 500 / JSONB·ARRAY 손상 방지).
    None은 nullable이면 DB가 처리하므로 통과."""
    if v is None:
        return
    pt = model.__table__.columns[key].type.python_type
    ok = True
    msg = ""
    if pt is bool:
        ok, msg = isinstance(v, bool), "must be a boolean"
    elif pt is int:
        ok, msg = (isinstance(v, int) and not isinstance(v, bool)), "must be an integer"
    elif pt in (float, Decimal):
        ok, msg = (isinstance(v, (int, float)) and not isinstance(v, bool)), "must be a number"
    elif pt is str:
        ok, msg = isinstance(v, str), "must be a string"
    elif pt is dict:  # JSONB
        ok, msg = isinstance(v, dict), "must be a JSON object"
    elif pt is list:  # ARRAY
        ok, msg = isinstance(v, list), "must be an array"
    if not ok:
        raise ValidationError(f"Field '{key}' {msg}")


def _clean(model: type, payload: dict, *, pk: str, require_pk: bool) -> dict:
    """허용 컬럼만 통과(미지 컬럼 422), PK 존재 + 컬럼 타입 검증."""
    allowed = _cols(model)
    unknown = set(payload) - allowed
    if unknown:
        raise ValidationError(f"Unknown fields: {', '.join(sorted(unknown))}")
    if require_pk and not payload.get(pk):
        raise ValidationError(f"'{pk}' is required")
    data = {k: v for k, v in payload.items() if k in allowed}
    for k, v in data.items():
        _check_type(model, k, v)
    return data


async def _commit_or_422(db) -> None:
    """commit 중 DB 타입/제약 위반(오버플로·NOT NULL 등)을 500이 아닌 422로."""
    try:
        await db.commit()
    except DBAPIError as e:
        await db.rollback()
        raise ValidationError("Invalid value for one or more fields") from e


@router.get("/{kind}")
async def list_master(kind: str, db: DbDep, _admin: SuperAdmin) -> list[dict]:
    """코드테이블 전체 행 조회."""
    model, pk = _resolve(kind)
    rows = (await db.execute(select(model).order_by(getattr(model, pk)))).scalars().all()
    return [_to_dict(model, r) for r in rows]


@router.post("/{kind}", status_code=201)
async def create_master(
    kind: str, db: DbDep, admin: SuperAdmin, payload: dict[str, Any] = Body(...)
) -> dict:
    """코드 행 생성."""
    model, pk = _resolve(kind)
    data = _clean(model, payload, pk=pk, require_pk=True)
    if await db.get(model, data[pk]):
        raise ConflictError(f"{pk}='{data[pk]}' already exists")
    row = model(**data)
    db.add(row)
    db.add(AuditLog(user_id=admin.id, farm_id=None, action="CREATE",
                    entity_type=f"master:{kind}", entity_id=None, new_value=data))
    await _commit_or_422(db)
    await db.refresh(row)
    return _to_dict(model, row)


@router.patch("/{kind}/{pk_value}")
async def update_master(
    kind: str, pk_value: str, db: DbDep, admin: SuperAdmin, payload: dict[str, Any] = Body(...)
) -> dict:
    """코드 행 수정 (PK 제외 컬럼)."""
    model, pk = _resolve(kind)
    row = await db.get(model, pk_value)
    if not row:
        raise NotFoundError(f"{pk}='{pk_value}' not found")
    data = _clean(model, payload, pk=pk, require_pk=False)
    data.pop(pk, None)  # PK 변경 불가
    before = {k: _to_dict(model, row)[k] for k in data}
    for k, v in data.items():
        setattr(row, k, v)
    db.add(AuditLog(user_id=admin.id, farm_id=None, action="UPDATE",
                    entity_type=f"master:{kind}", entity_id=None,
                    old_value=before, new_value=data))
    await _commit_or_422(db)
    await db.refresh(row)
    return _to_dict(model, row)


@router.delete("/{kind}/{pk_value}", status_code=204)
async def delete_master(kind: str, pk_value: str, db: DbDep, admin: SuperAdmin) -> None:
    """코드 행 삭제 (카탈로그 hard-delete)."""
    model, pk = _resolve(kind)
    row = await db.get(model, pk_value)
    if not row:
        raise NotFoundError(f"{pk}='{pk_value}' not found")
    await db.delete(row)
    db.add(AuditLog(user_id=admin.id, farm_id=None, action="DELETE",
                    entity_type=f"master:{kind}", entity_id=None, old_value={pk: pk_value}))
    await db.commit()
