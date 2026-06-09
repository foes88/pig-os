from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import UUIDMixin

_BOAR_STATUS = "^(ACTIVE|CULLED|DEAD|TRANSFERRED)$"
_ENTRY_TYPES = "^(PURCHASE|BORN|TRANSFER)$"
_SEMEN_QUALITY = "^(EXCELLENT|GOOD|FAIR|POOR)$"


class BoarCreate(BaseModel):
    ear_tag: str = Field(..., max_length=30)
    breed: str | None = Field(None, max_length=50)
    breed_company: str | None = Field(None, max_length=30)
    entry_date: date
    entry_type: str | None = Field(None, pattern=_ENTRY_TYPES)
    semen_quality: str | None = Field(None, pattern=_SEMEN_QUALITY)


class BoarUpdate(BaseModel):
    ear_tag: str | None = Field(None, max_length=30)
    breed: str | None = Field(None, max_length=50)
    breed_company: str | None = Field(None, max_length=30)
    status: str | None = Field(None, pattern=_BOAR_STATUS)
    semen_quality: str | None = Field(None, pattern=_SEMEN_QUALITY)


class BoarResponse(UUIDMixin):
    farm_id: UUID
    ear_tag: str
    breed: str | None
    breed_company: str | None
    status: str
    entry_date: datetime
    entry_type: str | None
    semen_quality: str | None
    created_at: datetime
