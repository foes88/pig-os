"""스코어카드 채점 — 국가 벤치마크(effective_metric_values) 대비 등급/기회 산정. 무가입 공개용."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# (metric_code, 요청필드, 기본방향) — 방향은 벤치마크 alert_direction 우선, 없으면 기본.
# below = 높을수록 좋음(값이 기준 아래로 떨어지면 경보) / above = 낮을수록 좋음.
_METRICS = [
    ("PSY", "psy", "below"),
    ("FARROWING_RATE", "farrowing_rate", "below"),
    ("BORN_ALIVE", "born_alive", "below"),
    ("WEANED_COUNT", "weaned", "below"),
    ("NPD", "npd", "above"),
]
_SCORE = {"TOP": 100, "GOOD": 80, "FAIR": 60, "LOW": 35}


async def _country_benchmarks(db: AsyncSession, country: str) -> dict[str, dict]:
    """국가(region) 벤치마크 dict — farm 없이 region/system 기본값. metric_code→{avg,top25,target,direction}."""
    rows = await db.execute(
        text("SELECT * FROM effective_metric_values(:farm, :region, :market)"),
        {"farm": "", "region": country.upper(), "market": "SYSTEM"},
    )
    out: dict[str, dict] = {}
    for r in rows:
        out[r.metric_code] = {
            "avg": float(r.benchmark_avg) if r.benchmark_avg is not None else None,
            "top25": float(r.benchmark_top25) if r.benchmark_top25 is not None else None,
            "target": float(r.target_value) if r.target_value is not None else None,
            "direction": str(r.alert_direction) if r.alert_direction else None,
        }
    return out


def _band(value: float, b: dict, direction: str) -> str:
    """value를 top25/avg/target 기준으로 TOP/GOOD/FAIR/LOW 밴딩. 벤치 없으면 NA."""
    top25, avg, target = b.get("top25"), b.get("avg"), b.get("target")
    if avg is None and top25 is None:
        return "NA"
    higher_better = direction != "above"
    def ge(a, bnd):  # higher-better 비교
        return a >= bnd if higher_better else a <= bnd
    if top25 is not None and ge(value, top25):
        return "TOP"
    if avg is not None and ge(value, avg):
        return "GOOD"
    if target is not None and ge(value, target):
        return "FAIR"
    # avg는 있으나 target 없음 → avg 미달은 LOW(단 top25/avg 사이는 위에서 GOOD 처리됨)
    return "FAIR" if target is None and top25 is not None and avg is None else "LOW"


async def compute_scorecard(db: AsyncSession, country: str, values: dict) -> dict:
    bm = await _country_benchmarks(db, country)
    metrics: list[dict] = []
    scored: list[int] = []
    for code, field, default_dir in _METRICS:
        v = values.get(field)
        if v is None:
            continue
        b = bm.get(code, {})
        direction = b.get("direction") or default_dir
        band = _band(float(v), b, direction)
        higher_better = direction != "above"
        avg = b.get("avg")
        gap = None
        if avg is not None:
            gap = round((avg - v) if higher_better else (v - avg), 2)  # +면 평균까지 개선여력
        m = {
            "code": code, "value": float(v),
            "avg": avg, "top25": b.get("top25"), "target": b.get("target"),
            "direction": direction, "band": band,
            "score": _SCORE.get(band, 0), "gap_to_avg": gap,
        }
        metrics.append(m)
        if band != "NA":
            scored.append(_SCORE[band])

    overall = round(sum(scored) / len(scored)) if scored else 0
    overall_band = ("TOP" if overall >= 90 else "GOOD" if overall >= 70
                    else "FAIR" if overall >= 50 else "LOW")
    # 개선 기회 = FAIR/LOW 밴드, 낮은 점수 우선(=여력 큰 순), 최대 3
    opps = sorted(
        [m for m in metrics if m["band"] in ("FAIR", "LOW")],
        key=lambda m: (m["score"], -(m["gap_to_avg"] or 0)),
    )[:3]
    return {
        "country": country.upper(),
        "overall_score": overall,
        "overall_band": overall_band,
        "metrics": metrics,
        "opportunities": [
            {"code": m["code"], "band": m["band"], "gap_to_avg": m["gap_to_avg"]}
            for m in opps
        ],
    }
