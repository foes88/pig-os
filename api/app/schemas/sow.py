from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import OrmBase, UUIDMixin


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
    ear_tag: str | None = Field(None, max_length=30)
    building_id: UUID | None = None
    breed: str | None = None
    rfid_tag: str | None = None


class SowResponse(UUIDMixin):
    farm_id: UUID
    ear_tag: str
    rfid_tag: str | None
    parity: int
    status: str
    breed: str | None
    breed_company: str | None
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
