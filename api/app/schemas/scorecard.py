"""무가입 농장 건강 스코어카드 — 공개(no-auth) 리드 퍼널.

농가가 국가 + 핵심 KPI 몇 개만 입력하면 국가 벤치마크(평균/상위25%) 대비 등급과
개선 기회를 즉시 반환. 문구는 프론트가 로케일별로 조합(백엔드는 구조화 데이터만).
"""
from pydantic import BaseModel, Field


class ScorecardRequest(BaseModel):
    country: str = Field(..., min_length=2, max_length=2, description="ISO2 국가코드(KR/US/...)")
    # 최소 1개 이상 값 제공(라우터에서 검증). 범위는 관대하게(현장 오입력 방지 수준).
    psy: float | None = Field(None, ge=0, le=45)
    npd: float | None = Field(None, ge=0, le=365)
    farrowing_rate: float | None = Field(None, ge=0, le=100)
    born_alive: float | None = Field(None, ge=0, le=30)
    weaned: float | None = Field(None, ge=0, le=30)


class ScorecardMetric(BaseModel):
    code: str                 # PSY / NPD / FARROWING_RATE / BORN_ALIVE / WEANED_COUNT
    value: float
    avg: float | None = None      # 국가 평균
    top25: float | None = None    # 국가 상위 25%
    target: float | None = None
    direction: str = "below"      # below=높을수록좋음(값<기준시 경보) / above=낮을수록좋음
    band: str                 # TOP / GOOD / FAIR / LOW / NA(벤치없음)
    score: int                # 0~100
    gap_to_avg: float | None = None   # 평균까지 남은 폭(개선여력, +면 아직 못미침)


class ScorecardOpportunity(BaseModel):
    code: str
    band: str
    gap_to_avg: float | None = None


class ScorecardResponse(BaseModel):
    country: str
    overall_score: int        # 0~100
    overall_band: str         # TOP / GOOD / FAIR / LOW
    metrics: list[ScorecardMetric] = []
    opportunities: list[ScorecardOpportunity] = []   # 최대 3, 나쁜 순
