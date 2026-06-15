from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import UUIDMixin


class SowCreate(BaseModel):
    ear_tag: str = Field(..., max_length=30)
    rfid_tag: str | None = Field(None, max_length=50)
    entry_date: date
    entry_type: str = Field(..., pattern="^(GILT|PURCHASE|TRANSFER|BORN)$")
    breed: str | None = None
    breed_company: str | None = None
    building_id: UUID | None = None
    parity: int = Field(default=0, ge=0, le=20)
    source_farm_id: UUID | None = None


class SowUpdate(BaseModel):
    """모돈 정보 수정 — DB 키값(id/farm_id)·이력성 필드 제외 전 항목 편집.

    status는 활성 상태(GILT/OPEN/PREGNANT/LACTATING/ACCIDENT)만 허용 —
    종료(CULLED/DEAD/SOLD/TRANSFER)는 /cull 엔드포인트(도폐사·판매 모달)로 처리.
    """
    ear_tag: str | None = Field(None, max_length=30)
    building_id: UUID | None = None
    breed: str | None = Field(None, max_length=50)
    breed_company: str | None = Field(None, max_length=30)
    genetics_id: str | None = Field(None, max_length=50)
    rfid_tag: str | None = Field(None, max_length=50)
    parity: int | None = Field(None, ge=0, le=20)
    entry_date: datetime | None = None
    entry_type: str | None = Field(None, pattern="^(GILT|PURCHASE|TRANSFER|BORN)$")
    status: str | None = Field(None, pattern="^(GILT|OPEN|PREGNANT|LACTATING|ACCIDENT)$")


_REMOVAL_TYPES = "^(CULLED|DEAD|SOLD|TRANSFER)$"
_REASON_CATEGORIES = (
    "^(REPRODUCTIVE|LAMENESS|DISEASE|AGE|PERFORMANCE|INJURY|BEHAVIOR|UNKNOWN|OTHER)$"
)

class SowCullRequest(BaseModel):
    """도폐사/판매 처리 — removals 이력 테이블에 기록."""
    removal_type: str = Field(..., pattern=_REMOVAL_TYPES)
    removal_date: date
    reason_category: str | None = Field(None, pattern=_REASON_CATEGORIES)
    reason_detail: str | None = Field(None, max_length=500)
    body_weight_kg: float | None = Field(None, gt=0, le=500)
    sale_price: float | None = Field(None, ge=0)
    sale_currency: str | None = Field(None, min_length=3, max_length=3)
    notes: str | None = None


class RemovalResponse(UUIDMixin):
    farm_id: UUID
    sow_id: UUID
    removal_date: date
    removal_type: str
    reason_category: str | None
    reason_detail: str | None
    body_weight_kg: float | None
    sale_price: float | None
    sale_currency: str | None
    created_at: datetime


class SowResponse(UUIDMixin):
    farm_id: UUID
    ear_tag: str
    rfid_tag: str | None
    parity: int
    status: str
    breed: str | None
    breed_company: str | None
    genetics_id: str | None
    entry_date: datetime
    entry_type: str
    building_id: UUID | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SowListFilter(BaseModel):
    status: str | None = None
    building_id: UUID | None = None
    parity_min: int | None = None
    parity_max: int | None = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=200)
