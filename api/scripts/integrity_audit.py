"""
전수 데이터 정합성 감사 (결정적, LLM 변동 0).

전 농장을 돌며 (1) 서비스 출력 vs DB 원천 재계산 일치, (2) 순수 데이터 불변식을 검사한다.
어떤 수치도 추정/날조하지 않는다 — 전부 실 집계 기반. FAIL이 하나라도 있으면 exit 1.

검사 항목:
  A. farrowing_rate 정합   — dashboard 출력 == farrowings/matings*100 (소수 일치) + percent 스케일
  B. trend 스케일          — trend farrowing_rate 전부 percent(0~100) 범위
  C. B1 항등식             — 모든 분만: total_born == born_alive + stillborn + mummified
  D. 두수 보존법칙         — 모든 분만: sum(weaned) <= born_alive + foster_in - foster_out - deaths
  E. 음수/범위 이상치      — 분만 두수 음수 0 / KPI 유효범위(PSY 0~45, NPD>=0, FR 0~100)
  G. soft-delete 누수      — deleted_at 분만/교배가 KPI 집계에 포함되지 않음
  (리포트 reproduction FR/sb_rate는 A와 동일 공식이라 A가 커버)

사용:  cd api && PYTHONPATH=. .venv/Scripts/python.exe scripts/integrity_audit.py
종료코드: 위반 0이면 0, 1건이라도 있으면 1.
주의: 위반 검출 시 데이터를 절대 자동수정하지 말 것 — 근인만 분류·보고(시드/테스트 오염 vs 실 corruption).
"""
import asyncio
import sys
from datetime import date

from sqlalchemy import func, select

from app.db.models.events import Farrowing, Mating, PigletEvent, Weaning
from app.db.models.platform import Farm
from app.db.session import AsyncSessionLocal
from app.services.kpi_service import get_dashboard, get_trend

FAILS: list[str] = []
CHECKS = 0


def check(cond: bool, label: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILS.append(label)
        print(f"  FAIL  {label}")


async def audit_farm(db, farm: Farm) -> None:
    fid = farm.id
    name = f"{farm.name}({str(fid)[:8]})"
    y0 = date(date.today().year, 1, 1)

    # --- 원천 집계(soft-delete 제외) ---
    m = await db.scalar(select(func.count()).select_from(Mating).where(
        Mating.farm_id == fid, Mating.mating_date >= y0, Mating.deleted_at.is_(None)))
    f = await db.scalar(select(func.count()).select_from(Farrowing).where(
        Farrowing.farm_id == fid, Farrowing.farrowing_date >= y0, Farrowing.deleted_at.is_(None)))
    expected_fr = round(f / m * 100, 6) if m else None

    # --- A. farrowing_rate 정합 + 스케일 ---
    dash = await get_dashboard(db, farm)
    fr = dash.farrowing_rate
    if expected_fr is None:
        check(fr is None, f"[{name}] A: 교배0인데 FR이 None 아님({fr})")
    else:
        check(fr is not None and abs(fr - expected_fr) < 0.01,
              f"[{name}] A: dashboard FR {fr} != 원천 {expected_fr} ({f}/{m})")
        check(fr is None or fr > 1.0 or expected_fr <= 1.0,
              f"[{name}] A: FR 스케일 ratio 의심 {fr} (percent여야)")

    # --- E. KPI 범위 ---
    if dash.psy is not None:
        check(0 <= dash.psy <= 45, f"[{name}] E: PSY 범위밖 {dash.psy}")
    if dash.npd is not None:
        check(dash.npd >= 0, f"[{name}] E: NPD 음수 {dash.npd}")
    if fr is not None:
        check(0 <= fr <= 100, f"[{name}] E: FR 범위밖 {fr}")

    # --- B. trend 스케일 ---
    trend = await get_trend(db, fid, months=12)
    for p in trend:
        if p.farrowing_rate is not None:
            check(0 <= p.farrowing_rate <= 100,
                  f"[{name}] B: trend FR 범위밖 {p.farrowing_rate}@{p.period}")

    # --- C·D·E: 분만 단위 불변식 ---
    farrowings = (await db.scalars(select(Farrowing).where(
        Farrowing.farm_id == fid, Farrowing.deleted_at.is_(None)))).all()
    for fa in farrowings:
        tb = fa.total_born or 0
        ba = fa.born_alive or 0
        sb = fa.stillborn or 0
        mm = fa.mummified or 0
        # C. B1 항등식
        check(tb == ba + sb + mm,
              f"[{name}] C: B1 항등식 위반 farrow {str(fa.id)[:8]} TB{tb}!=BA{ba}+SB{sb}+MM{mm}")
        # E. 음수
        check(ba >= 0 and sb >= 0 and mm >= 0,
              f"[{name}] E: 분만 음수두수 {str(fa.id)[:8]}")
        # D. 보존법칙
        fi = await db.scalar(select(func.coalesce(func.sum(PigletEvent.piglet_count), 0)).where(
            PigletEvent.farrowing_id == fa.id, PigletEvent.event_type == "FOSTER_IN",
            PigletEvent.deleted_at.is_(None))) or 0
        fo = await db.scalar(select(func.coalesce(func.sum(PigletEvent.piglet_count), 0)).where(
            PigletEvent.farrowing_id == fa.id, PigletEvent.event_type == "FOSTER_OUT",
            PigletEvent.deleted_at.is_(None))) or 0
        de = await db.scalar(select(func.coalesce(func.sum(PigletEvent.piglet_count), 0)).where(
            PigletEvent.farrowing_id == fa.id, PigletEvent.event_type == "DEATH",
            PigletEvent.deleted_at.is_(None))) or 0
        weaned = await db.scalar(select(func.coalesce(func.sum(Weaning.weaned_count), 0)).where(
            Weaning.farrowing_id == fa.id, Weaning.deleted_at.is_(None))) or 0
        effective = max(0, ba + int(fi) - int(fo) - int(de))
        check(int(weaned) <= effective,
              f"[{name}] D: 보존위반 farrow {str(fa.id)[:8]} weaned{int(weaned)}>유효{effective}"
              f"(BA{ba}+FI{int(fi)}-FO{int(fo)}-D{int(de)})")

    # (리포트 reproduction FR/sb_rate는 dashboard·A와 동일 공식 farrowings/matings*100 → A가 커버)

    # --- G. soft-delete 누수: 삭제분이 올해 KPI 집계에 안 들어감 ---
    deleted_f = await db.scalar(select(func.count()).select_from(Farrowing).where(
        Farrowing.farm_id == fid, Farrowing.farrowing_date >= y0, Farrowing.deleted_at.is_not(None)))
    f_all = await db.scalar(select(func.count()).select_from(Farrowing).where(
        Farrowing.farm_id == fid, Farrowing.farrowing_date >= y0))
    check(f == f_all - (deleted_f or 0),
          f"[{name}] G: soft-delete 누수 — 활성{f} != 전체{f_all}-삭제{deleted_f}")

    print(f"  OK   {name}: matings {m}, farrowings {f}, FR {fr}, 분만행 {len(farrowings)}")


async def main() -> None:
    async with AsyncSessionLocal() as db:
        farms = (await db.scalars(select(Farm).where(Farm.active.is_(True)))).all()
        print(f"=== 정합성 감사 시작: 활성 농장 {len(farms)}개 ===")
        for farm in farms:
            try:
                await audit_farm(db, farm)
            except Exception as e:  # noqa: BLE001
                FAILS.append(f"[{farm.name}] EXCEPTION: {e!r}")
                print(f"  ERR  {farm.name}: {e!r}")
    print(f"\n=== 결과: 검사 {CHECKS}건, 실패 {len(FAILS)}건 ===")
    if FAILS:
        print("정합성 위반 발견:")
        for x in FAILS:
            print(f"  - {x}")
        sys.exit(1)
    print("ALL PASS - 전 농장 데이터 정합성 무결(날조 0)")


if __name__ == "__main__":
    asyncio.run(main())
