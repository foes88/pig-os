"""
Public endpoint — no auth required.
Receives pilot signup from pigos.io landing page.
"""
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from app.db.session import get_db
from app.db.models.pilot_signup import PilotSignup

router = APIRouter(prefix="/pilot-signups", tags=["public"])

VALID_FARM_SIZES = {"under_100", "100_500", "500_1000", "1000_plus"}
VALID_ROLES = {"owner", "manager", "vet", "partner"}
VALID_LANGS = {"en", "ko", "zh", "es", "vi", "th"}
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class PilotSignupIn(BaseModel):
    name: str
    email: str
    farm_size: str
    country: str
    role: str
    lang: str = "en"

    @field_validator("name", "email", "country", mode="before")
    @classmethod
    def strip_str(cls, v: str) -> str:
        return v.strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError("invalid email")
        return v.lower()

    @field_validator("farm_size")
    @classmethod
    def validate_farm_size(cls, v: str) -> str:
        if v not in VALID_FARM_SIZES:
            raise ValueError("invalid farm_size")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in VALID_ROLES:
            raise ValueError("invalid role")
        return v

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        return v if v in VALID_LANGS else "en"


class PilotSignupOut(BaseModel):
    success: bool


@router.post("", response_model=PilotSignupOut, status_code=status.HTTP_201_CREATED)
async def create_pilot_signup(
    body: PilotSignupIn,
    db: AsyncSession = Depends(get_db),
) -> PilotSignupOut:
    signup = PilotSignup(
        name=body.name,
        email=body.email,
        farm_size=body.farm_size,
        country=body.country,
        role=body.role,
        lang=body.lang,
        status="pending",
    )
    db.add(signup)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="duplicate_email")
    return PilotSignupOut(success=True)
