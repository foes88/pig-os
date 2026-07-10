"""
공개 설정 엔드포인트 (pre-auth) — 웹/모바일이 온보딩 전에 조회.

`GET /api/v1/config/countries` : 서비스 대상 국가 + 기본값(통화/단위/타임존/언어/전화).
단일 소스 `app.core.countries.COUNTRY_CONFIG` 를 그대로 노출 → 국가 추가 시
백엔드만 고치면 클라 재배포 없이 반영.
"""
from fastapi import APIRouter

from app.core.countries import list_countries

router = APIRouter(prefix="/config", tags=["Config"])


@router.get("/countries")
async def get_countries() -> list[dict]:
    """서비스 대상 국가 목록. 각 항목: code, name, timezone, currency, unit_system, dial, language."""
    return list_countries()
