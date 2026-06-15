"""Device(푸시 토큰) 스키마 — G2."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import UUIDMixin


class DeviceRegister(BaseModel):
    platform: str = Field(..., pattern="^(ANDROID|IOS|WEB)$")
    token: str = Field(..., min_length=1, max_length=255)
    app_version: str | None = Field(None, max_length=20)


class DeviceResponse(UUIDMixin):
    user_id: UUID
    platform: str
    app_version: str | None
    created_at: datetime
    last_seen_at: datetime | None
