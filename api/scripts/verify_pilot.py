#!/usr/bin/env python
"""
파일럿 후속 Phase C — 수치 정합성 검증 (적재된 pigos DB ↔ 피그플랜 raw CSV).

검증 범위:
- 농장×연도: PigOS PSY numerator(이유두수), NPD(WEI), FR(분만/교배) ↔ raw CSV
- DB 무결성: 두수 항등식, 교배<분만<이유, 미래일, LACTATING 상태 고아
- import 격리 proxy: raw 이벤트 수와 PigOS replay 이벤트 수 gap

전제: import_pigplan(적재) 완료. 로컬 Docker pigos DB.
실행: cd api && uv run python -m scripts.verify_pilot
"""
from __future__ import annotations

import argparse
import asyncio
import logging
from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from statistics import fmean
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.services.kpi_service import calculate_npd, calculate_psy
from scripts.import_pigplan import DEFAULT_CSV, fnum, load_csv, pdate
from scripts.pilot_common import PILOT_FARMS, farm_uuid

# 파일럿 통과 기준: 문서의 Phase C 기준과 동일하게 유지.
WEANED_TOL_PCT = 3.0
NPD_TOL_DAYS = 2.0
FR_TOL_PP = 3.0
# 교배 gap은 구조적: 피그플랜은 발정당 교배를 여러 건 기록, PigOS는 사이클당 1교배로 정규화
# → 1:1 비교 불가 → 게이트에서 제외하고 정보로만 출력.
# 분만/이유 gap은 replay 격리율 proxy로 2% 이하를 유지.
REPLAY_GAP_TOL_PCT = 2.0


@dataclass(frozen=True)
class RawFarmMetrics:
    mating_counts: dict[int, int]
    farrowing_counts: dict[int, int]
    weaning_events: dict[int, int]
    weaned_heads: dict[int, int]
    npd_avg: dict[int, float]


@dataclass(frozen=True)
class PigosYearCounts:
    matings: int
    farrowings: int
    weaning_events: int
    weaned_heads: int


@dataclass(frozen=True)
class YearScore:
    farm_no: int
    year: int
    pigos_weaned: int
    raw_weaned: int
    pigos_psy: float | None
    pigos_npd: float | None
    raw_npd: float | None
    pigos_fr: float | None
    raw_fr: float | None

    @property
    def weaned_diff_pct(self) -> float:
        return _pct_diff(self.pigos_weaned, self.raw_weaned)

    @property
    def npd_diff_days(self) -> float | None:
        if self.pigos_npd is None or self.raw_npd is None:
            return None
        return abs(self.pigos_npd - self.raw_npd)

    @property
    def fr_diff_pp(self) -> float | None:
        if self.pigos_fr is None or self.raw_fr is None:
            return None
        return abs(self.pigos_fr - self.raw_fr)

    @property
    def ok(self) -> bool:
        psy_ok = self.weaned_diff_pct <= WEANED_TOL_PCT and (self.raw_weaned == 0 or self.pigos_psy is not None)
        npd_ok = self.raw_npd is None or (self.pigos_npd is not None and self.npd_diff_days <= NPD_TOL_DAYS)
        fr_ok = self.raw_fr is None or (self.pigos_fr is not None and self.fr_diff_pp <= FR_TOL_PP)
        return psy_ok and npd_ok and fr_ok


@dataclass(frozen=True)
class IntegrityScore:
    litter_identity: int
    status_orphan: int
    date_sequence: int
    future_events: int

    @property
    def ok(self) -> bool:
        return self.litter_identity == 0 and self.status_orphan == 0 and self.date_sequence == 0 and self.future_events == 0


@dataclass(frozen=True)
class EventGapScore:
    raw_matings: int
    pigos_matings: int
    raw_farrowings: int
    pigos_farrowings: int
    raw_weanings: int
    pigos_weanings: int

    @property
    def mating_gap_pct(self) -> float:
        return _pct_diff(self.pigos_matings, self.raw_matings)

    @property
    def farrowing_gap_pct(self) -> float:
        return _pct_diff(self.pigos_farrowings, self.raw_farrowings)

    @property
    def weaning_gap_pct(self) -> float:
        return _pct_diff(self.pigos_weanings, self.raw_weanings)

    @property
    def ok(self) -> bool:
        # 교배 gap은 구조적(발정당 다건 기록) → 게이트 제외·정보용. 분만/이유만 replay 완전성 검사.
        return (
            self.farrowing_gap_pct <= REPLAY_GAP_TOL_PCT
            and self.weaning_gap_pct <= REPLAY_GAP_TOL_PCT
        )


@dataclass(frozen=True)
class FarmScorecard:
    farm_no: int
    loaded_sows: int
    years: list[YearScore]
    integrity: IntegrityScore
    event_gap: EventGapScore

    @property
    def ok(self) -> bool:
        return self.loaded_sows > 0 and bool(self.years) and all(y.ok for y in self.years) and self.integrity.ok and self.event_gap.ok

    def failure_reasons(self) -> list[str]:
        reasons: list[str] = []
        if self.loaded_sows <= 0:
            reasons.append(f"farm {self.farm_no}: no imported sows")
        if not self.years:
            reasons.append(f"farm {self.farm_no}: no comparable years")
        for score in self.years:
            if not score.ok:
                reasons.append(
                    f"farm {self.farm_no} {score.year}: weaned_diff={score.weaned_diff_pct:.1f}% "
                    f"npd_diff={_fmt(score.npd_diff_days)} fr_diff={_fmt(score.fr_diff_pp)}"
                )
        if not self.integrity.ok:
            reasons.append(
                f"farm {self.farm_no}: integrity identity={self.integrity.litter_identity} "
                f"orphan={self.integrity.status_orphan} date_sequence={self.integrity.date_sequence} "
                f"future={self.integrity.future_events}"
            )
        if not self.event_gap.ok:
            reasons.append(
                f"farm {self.farm_no}: event_gap mating={self.event_gap.mating_gap_pct:.1f}% "
                f"farrowing={self.event_gap.farrowing_gap_pct:.1f}% weaning={self.event_gap.weaning_gap_pct:.1f}%"
            )
        return reasons


def _pct_diff(pigos: int, raw: int) -> float:
    if raw == 0:
        return 0.0 if pigos == 0 else 100.0
    return abs(pigos - raw) / raw * 100.0


def _rate(success: int, total: int) -> float | None:
    return round(success / total * 100.0, 1) if total else None


def _fmt(value: float | None) -> str:
    return "NA" if value is None else f"{value:.1f}"


def raw_metrics(csv_dir: Path, farm_no: int) -> RawFarmMetrics:
    mating_counts: dict[int, int] = defaultdict(int)
    farrowing_counts: dict[int, int] = defaultdict(int)
    weaning_events: dict[int, int] = defaultdict(int)
    weaned_heads: dict[int, int] = defaultdict(int)
    matings_by_pig: dict[str, list[date]] = defaultdict(list)
    npd_values: dict[int, list[int]] = defaultdict(list)

    for row in load_csv(csv_dir, "TB_GYOBAE", {farm_no}):
        d = pdate(row.get("wk_dt"))
        if not d:
            continue
        mating_counts[d.year] += 1
        matings_by_pig[row["pig_no"]].append(d)
    for dates in matings_by_pig.values():
        dates.sort()

    for row in load_csv(csv_dir, "TB_BUNMAN", {farm_no}):
        d = pdate(row.get("wk_dt"))
        if d:
            farrowing_counts[d.year] += 1

    npd_cutoff = date.today() - timedelta(days=60)
    for row in load_csv(csv_dir, "TB_EU", {farm_no}):
        d = pdate(row.get("wk_dt"))
        if not d:
            continue
        weaning_events[d.year] += 1
        weaned_heads[d.year] += int(fnum(row.get("dusu")))
        pig_matings = matings_by_pig.get(row["pig_no"], [])
        idx = bisect_right(pig_matings, d)
        if idx < len(pig_matings) and pig_matings[idx] <= d + timedelta(days=60):
            npd_values[d.year].append((pig_matings[idx] - d).days)
        elif d <= npd_cutoff:
            npd_values[d.year].append(60)

    return RawFarmMetrics(
        mating_counts=dict(mating_counts),
        farrowing_counts=dict(farrowing_counts),
        weaning_events=dict(weaning_events),
        weaned_heads=dict(weaned_heads),
        npd_avg={year: round(fmean(values), 2) for year, values in npd_values.items() if values},
    )


async def _pigos_year_counts(db: AsyncSession, farm_id: UUID, year: int) -> PigosYearCounts:
    def count_sql(table: str, date_col: str):
        return text(
            f"SELECT COUNT(*) FROM {table} WHERE farm_id=:farm_id AND deleted_at IS NULL "
            f"AND EXTRACT(YEAR FROM {date_col})=:year"
        )

    matings = await db.scalar(count_sql("matings", "mating_date"), {"farm_id": str(farm_id), "year": year})
    farrowings = await db.scalar(count_sql("farrowings", "farrowing_date"), {"farm_id": str(farm_id), "year": year})
    weaning_events = await db.scalar(count_sql("weanings", "weaning_date"), {"farm_id": str(farm_id), "year": year})
    weaned_heads = await db.scalar(text(
        "SELECT COALESCE(SUM(weaned_count),0) FROM weanings WHERE farm_id=:farm_id "
        "AND deleted_at IS NULL AND EXTRACT(YEAR FROM weaning_date)=:year"
    ), {"farm_id": str(farm_id), "year": year})
    return PigosYearCounts(int(matings or 0), int(farrowings or 0), int(weaning_events or 0), int(weaned_heads or 0))


async def _integrity(db: AsyncSession, farm_id: UUID) -> IntegrityScore:
    litter_identity = await db.scalar(text(
        "SELECT COUNT(*) FROM farrowings WHERE farm_id=:farm_id AND deleted_at IS NULL "
        "AND total_born <> born_alive + stillborn + mummified"
    ), {"farm_id": str(farm_id)})
    status_orphan = await db.scalar(text(
        "SELECT COUNT(*) FROM sows WHERE farm_id=:farm_id AND status='LACTATING' AND deleted_at IS NULL "
        "AND id NOT IN (SELECT sow_id FROM farrowings WHERE farm_id=:farm_id AND deleted_at IS NULL)"
    ), {"farm_id": str(farm_id)})
    date_sequence = await db.scalar(text(
        "SELECT COALESCE(SUM(cnt),0) FROM ("
        "SELECT COUNT(*) AS cnt FROM farrowings f JOIN matings m ON m.id=f.mating_id "
        "WHERE f.farm_id=:farm_id AND f.deleted_at IS NULL AND m.deleted_at IS NULL "
        "AND f.farrowing_date <= m.mating_date "
        "UNION ALL "
        "SELECT COUNT(*) AS cnt FROM weanings w JOIN farrowings f ON f.id=w.farrowing_id "
        "WHERE w.farm_id=:farm_id AND w.deleted_at IS NULL AND f.deleted_at IS NULL "
        "AND w.weaning_date <= f.farrowing_date"
        ") x"
    ), {"farm_id": str(farm_id)})
    future_events = await db.scalar(text(
        "SELECT COALESCE(SUM(cnt),0) FROM ("
        "SELECT COUNT(*) AS cnt FROM matings WHERE farm_id=:farm_id AND deleted_at IS NULL AND mating_date > CURRENT_DATE "
        "UNION ALL SELECT COUNT(*) AS cnt FROM farrowings WHERE farm_id=:farm_id AND deleted_at IS NULL AND farrowing_date > CURRENT_DATE "
        "UNION ALL SELECT COUNT(*) AS cnt FROM weanings WHERE farm_id=:farm_id AND deleted_at IS NULL AND weaning_date > CURRENT_DATE "
        "UNION ALL SELECT COUNT(*) AS cnt FROM reproductive_events WHERE farm_id=:farm_id AND deleted_at IS NULL AND event_date > CURRENT_DATE "
        "UNION ALL SELECT COUNT(*) AS cnt FROM piglet_events WHERE farm_id=:farm_id AND deleted_at IS NULL AND event_date > CURRENT_DATE"
        ") x"
    ), {"farm_id": str(farm_id)})
    return IntegrityScore(int(litter_identity or 0), int(status_orphan or 0), int(date_sequence or 0), int(future_events or 0))


async def _event_gap(db: AsyncSession, farm_id: UUID, raw: RawFarmMetrics) -> EventGapScore:
    pigos_matings = await db.scalar(text("SELECT COUNT(*) FROM matings WHERE farm_id=:farm_id AND deleted_at IS NULL"), {"farm_id": str(farm_id)})
    pigos_farrowings = await db.scalar(text("SELECT COUNT(*) FROM farrowings WHERE farm_id=:farm_id AND deleted_at IS NULL"), {"farm_id": str(farm_id)})
    pigos_weanings = await db.scalar(text("SELECT COUNT(*) FROM weanings WHERE farm_id=:farm_id AND deleted_at IS NULL"), {"farm_id": str(farm_id)})
    return EventGapScore(
        raw_matings=sum(raw.mating_counts.values()),
        pigos_matings=int(pigos_matings or 0),
        raw_farrowings=sum(raw.farrowing_counts.values()),
        pigos_farrowings=int(pigos_farrowings or 0),
        raw_weanings=sum(raw.weaning_events.values()),
        pigos_weanings=int(pigos_weanings or 0),
    )


async def build_scorecards(
    csv_dir: Path = DEFAULT_CSV,
    farms: tuple[int, ...] = PILOT_FARMS,
) -> list[FarmScorecard]:
    scorecards: list[FarmScorecard] = []
    async with AsyncSessionLocal() as db:
        for farm_no in farms:
            farm_id = farm_uuid(farm_no)
            loaded_sows = await db.scalar(text("SELECT COUNT(*) FROM sows WHERE farm_id=:farm_id"), {"farm_id": str(farm_id)})
            raw = raw_metrics(csv_dir, farm_no)
            years = sorted(
                year for year in (
                    set(raw.mating_counts) | set(raw.farrowing_counts) | set(raw.weaning_events) | set(raw.weaned_heads)
                )
                if year >= 2020
            )
            year_scores: list[YearScore] = []
            for year in years:
                counts = await _pigos_year_counts(db, farm_id, year)
                psy = await calculate_psy(db, farm_id, year)
                # calculate_npd(여집합 NPD, rolling 12개월) — ref_date 기준. 연도 검증이므로 연말일자를 기준일로.
                npd = await calculate_npd(db, farm_id, date(year, 12, 31))
                year_scores.append(YearScore(
                    farm_no=farm_no,
                    year=year,
                    pigos_weaned=counts.weaned_heads,
                    raw_weaned=raw.weaned_heads.get(year, 0),
                    pigos_psy=(psy.psy if psy else None),
                    pigos_npd=npd.avg_npd,
                    raw_npd=raw.npd_avg.get(year),
                    pigos_fr=_rate(counts.farrowings, counts.matings),
                    raw_fr=_rate(raw.farrowing_counts.get(year, 0), raw.mating_counts.get(year, 0)),
                ))
            scorecards.append(FarmScorecard(
                farm_no=farm_no,
                loaded_sows=int(loaded_sows or 0),
                years=year_scores,
                integrity=await _integrity(db, farm_id),
                event_gap=await _event_gap(db, farm_id, raw),
            ))
    return scorecards


def print_scorecards(scorecards: list[FarmScorecard]) -> None:
    print("=== Phase C 수치 정합성 스코어카드 ===")
    for card in scorecards:
        print(f"\n농장 {card.farm_no} (모돈 {card.loaded_sows}두) — {'PASS' if card.ok else 'FAIL'}")
        print(f"  {'YR':4s} {'wean P/R':>15s} {'diff%':>7s} {'PSY':>7s} {'NPD P/R':>15s} {'FR P/R':>15s}")
        for y in card.years:
            print(
                f"  {y.year:<4d} {f'{y.pigos_weaned}/{y.raw_weaned}':>15s} {y.weaned_diff_pct:>6.1f}% "
                f"{_fmt(y.pigos_psy):>7s} {f'{_fmt(y.pigos_npd)}/{_fmt(y.raw_npd)}':>15s} "
                f"{f'{_fmt(y.pigos_fr)}/{_fmt(y.raw_fr)}':>15s}"
            )
        print(
            "  무결성: "
            f"두수항등식={card.integrity.litter_identity} "
            f"상태고아={card.integrity.status_orphan} "
            f"날짜역전={card.integrity.date_sequence} "
            f"미래일={card.integrity.future_events}"
        )
        print(
            "  replay gap: "
            f"mating {card.event_gap.pigos_matings}/{card.event_gap.raw_matings} ({card.event_gap.mating_gap_pct:.1f}%) · "
            f"farrowing {card.event_gap.pigos_farrowings}/{card.event_gap.raw_farrowings} ({card.event_gap.farrowing_gap_pct:.1f}%) · "
            f"weaning {card.event_gap.pigos_weanings}/{card.event_gap.raw_weanings} ({card.event_gap.weaning_gap_pct:.1f}%)"
        )
        for reason in card.failure_reasons():
            print(f"  - {reason}")
    passed = sum(1 for card in scorecards if card.ok)
    print(f"\n결과: {passed}/{len(scorecards)} farms PASS")


async def main() -> int:
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-dir", default=str(DEFAULT_CSV))
    parser.add_argument("--farm", default="ALL", help="ALL 또는 FARM_NO")
    args = parser.parse_args()

    farms = PILOT_FARMS if args.farm.upper() == "ALL" else (int(args.farm),)
    scorecards = await build_scorecards(Path(args.csv_dir), farms)
    print_scorecards(scorecards)
    return 0 if scorecards and all(card.ok for card in scorecards) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
