"""
서비스 대상 국가 설정 — **단일 소스(Single Source of Truth)**.

국가가 계속 추가될 수 있으므로 이 파일 하나만 고치면 전체(백엔드 온보딩 파생 +
공개 엔드포인트 `GET /api/v1/config/countries`를 통해 웹/모바일)까지 반영된다.
클라이언트는 이 엔드포인트를 fetch → 재배포 없이 신규 국가 노출.

각 국가는 country 선택 시 자동 프리필되는 기본값을 정의:
- timezone     : 대표 타임존(날짜 경계 정확 — _farm_today)
- currency     : ISO 4217 (farms.currency, 원가/수익 리포트 단위)
- unit_system  : METRIC | IMPERIAL (US만 IMPERIAL — 체중 lb/온도 °F)
- dial         : 국제전화 코드
- language     : 기본 UI 로케일(사용자가 이후 변경 가능; ko는 관리자 전용 정책은 프론트에서 적용)
"""
from __future__ import annotations

# 순서 = 드롭다운 표기 순서. 신규 국가는 여기에 한 줄 추가하면 끝.
COUNTRY_CONFIG: dict[str, dict] = {
    "KR": {"name": "South Korea",   "timezone": "Asia/Seoul",         "currency": "KRW", "unit_system": "METRIC",   "dial": "+82", "language": "ko"},
    "US": {"name": "United States", "timezone": "America/Chicago",    "currency": "USD", "unit_system": "IMPERIAL", "dial": "+1",  "language": "en"},
    "CN": {"name": "China",         "timezone": "Asia/Shanghai",      "currency": "CNY", "unit_system": "METRIC",   "dial": "+86", "language": "zh"},
    "VN": {"name": "Vietnam",       "timezone": "Asia/Ho_Chi_Minh",   "currency": "VND", "unit_system": "METRIC",   "dial": "+84", "language": "vi"},
    "TH": {"name": "Thailand",      "timezone": "Asia/Bangkok",       "currency": "THB", "unit_system": "METRIC",   "dial": "+66", "language": "th"},
    "PH": {"name": "Philippines",   "timezone": "Asia/Manila",        "currency": "PHP", "unit_system": "METRIC",   "dial": "+63", "language": "en"},
    "BR": {"name": "Brazil",        "timezone": "America/Sao_Paulo",  "currency": "BRL", "unit_system": "METRIC",   "dial": "+55", "language": "pt"},
    "MX": {"name": "Mexico",        "timezone": "America/Mexico_City","currency": "MXN", "unit_system": "METRIC",   "dial": "+52", "language": "es"},
    "CL": {"name": "Chile",         "timezone": "America/Santiago",   "currency": "CLP", "unit_system": "METRIC",   "dial": "+56", "language": "es"},
    "RU": {"name": "Russia",        "timezone": "Europe/Moscow",      "currency": "RUB", "unit_system": "METRIC",   "dial": "+7",  "language": "ru"},
}

# 국가 미지정/미등록 시 폴백(온보딩이 낯선 country 코드를 받아도 깨지지 않게).
DEFAULT_CONFIG: dict = {
    "name": None, "timezone": "UTC", "currency": "USD",
    "unit_system": "METRIC", "dial": "", "language": "en",
}


def get_country(code: str | None) -> dict:
    """ISO alpha-2 → 국가 설정. 미등록이면 DEFAULT_CONFIG."""
    if not code:
        return DEFAULT_CONFIG
    return COUNTRY_CONFIG.get(code.upper(), DEFAULT_CONFIG)


def list_countries() -> list[dict]:
    """공개 엔드포인트용 정렬 목록. `code` 포함."""
    return [{"code": code, **cfg} for code, cfg in COUNTRY_CONFIG.items()]
