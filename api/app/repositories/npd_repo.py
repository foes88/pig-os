"""WEI(이유→재교배 간격) 조회 — as_of 기준 결정론.

계약 위반이었던 것:
    호출 계약  service(as_of) 기준 계산
    실제 계산  v_sow_npd 안의 CURRENT_DATE 기준 계산

PostgreSQL 뷰는 파라미터를 받을 수 없으므로 뷰를 고치는 게 아니라, 계산 경로를
:as_of 를 명시적으로 바인드하는 repository 쿼리로 옮긴다.
v_sow_npd 는 "오늘 기준 convenience view" 로 남지만 계산 경로에서는 쓰지 않는다.

as_of 의 의미(둘 다 필요):
  ① 유휴 판정 기준일 — weaning_date <= as_of - 60 이면 60 cap
  ② 관측 시점        — as_of 이후의 교배는 아직 일어나지 않은 사건이므로 보지 않는다
     (②가 없으면 2026-06-30 시점 NPD 를 오늘 재계산할 때 7월 교배가 섞여
      월마감·과거 스냅샷이 재현되지 않는다. as_of=오늘이면 결과는 동일하다.)

경계(기존 뷰 의미 그대로 보존): 이유 후 60일 이상 미재교배 → 60 cap,
60일 미만 → NULL(아직 정상 WEI 구간), 재교배 완료 → LEAST(60, 실제 간격).

sow.deleted_at 필터 없음(C2, f7a1c3e5b9d0 정본): 도폐사는 cull_sow 가 소프트삭제하므로
필터를 걸면 도태 모돈이 도태 전 남긴 이유 이력이 통째로 빠져 표본이 급감한다.
완료된 이유는 사실이다. weaning/mating 의 deleted_at 필터는 유지.
"""
from datetime import date
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# 이유 1건 = 1행. wei_days 는 NULL 가능. 필요한 곳에서 CTE 로 감싸 쓴다.
# ★ CURRENT_DATE/now() 사용 금지 — 모든 날짜 판정은 :as_of 기준.
WEI_ROWS_SQL = """
SELECT s.id AS sow_id, s.farm_id, w.id AS weaning_id, w.weaning_date,
       m_next.mating_date AS next_mating_date,
       CASE
           WHEN m_next.mating_date IS NOT NULL THEN LEAST(60, m_next.mating_date - w.weaning_date)
           WHEN w.weaning_date <= (:as_of)::date - 60 THEN 60
           ELSE NULL
       END AS wei_days
FROM sows s
JOIN weanings w ON w.sow_id = s.id AND w.deleted_at IS NULL
LEFT JOIN LATERAL (
    SELECT m.mating_date FROM matings m
    WHERE m.sow_id = s.id
      AND m.mating_date > w.weaning_date
      AND m.mating_date <= LEAST(w.weaning_date + 60, (:as_of)::date)
      AND m.deleted_at IS NULL
    ORDER BY m.mating_date LIMIT 1
) m_next ON TRUE
WHERE s.farm_id = :farm_id
  AND w.weaning_date <= (:as_of)::date
"""

_AVG = text(f"SELECT AVG(wei_days) AS w FROM ({WEI_ROWS_SQL}) t "
            "WHERE wei_days IS NOT NULL AND weaning_date BETWEEN :s AND :e")

_SUM = text(f"SELECT coalesce(sum(wei_days), 0) FROM ({WEI_ROWS_SQL}) t "
            "WHERE wei_days IS NOT NULL AND wei_days > 0 AND weaning_date BETWEEN :s AND :e")


async def avg_wei_days(
    db: AsyncSession, farm_id: UUID, *, start: date, end: date, as_of: date,
) -> float | None:
    """기간 내 이유건의 평균 WEI. 값 없으면 None."""
    row = (await db.execute(
        _AVG, {"farm_id": str(farm_id), "s": start, "e": end, "as_of": as_of},
    )).fetchone()
    return float(row.w) if row and row.w is not None else None


async def sum_wei_days(
    db: AsyncSession, farm_id: UUID, *, start: date, end: date, as_of: date,
) -> float:
    """기간 내 총 지연일 합(손실 추정용). 값 없으면 0."""
    return float((await db.execute(
        _SUM, {"farm_id": str(farm_id), "s": start, "e": end, "as_of": as_of},
    )).scalar() or 0)
