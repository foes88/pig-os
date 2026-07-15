"""무가입 농장 건강 스코어카드 — 공개(no-auth) 리드 퍼널 엔드포인트.

pigos.io/scorecard 에서 국가 + KPI 몇 개 입력 → 국가 벤치마크 대비 등급/기회 즉시 반환.
가입 전환 미끼. 데이터 저장 없음(순수 계산). 남용 방지는 게이트웨이/레이트리밋 층에서.
"""
from fastapi import APIRouter

from app.core.dependencies import DbDep
from app.core.exceptions import ValidationError
from app.schemas.scorecard import ScorecardRequest, ScorecardResponse
from app.services import scorecard_service

router = APIRouter(prefix="/scorecard", tags=["public"])


@router.post("", response_model=ScorecardResponse)
async def compute_scorecard(body: ScorecardRequest, db: DbDep) -> ScorecardResponse:
    """국가 + 입력 KPI로 벤치마크 대비 스코어카드 산정(무가입). 최소 1개 지표 필요."""
    values = {
        "psy": body.psy, "npd": body.npd, "farrowing_rate": body.farrowing_rate,
        "born_alive": body.born_alive, "weaned": body.weaned,
    }
    if all(v is None for v in values.values()):
        raise ValidationError("Provide at least one KPI value (psy/npd/farrowing_rate/born_alive/weaned)")
    result = await scorecard_service.compute_scorecard(db, body.country, values)
    return ScorecardResponse(**result)
