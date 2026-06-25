"""
operational_default 레지스트리 시드 — 룰 코드에 인라인된 글로벌 임상 임계를 '값 그대로' 이전.

A-하이브리드(handoff/operational_default_inventory.md): 발화 기준(threshold)의 거처를
코드 인라인 → 명시 레지스트리로 옮긴다. **신규 생성 0, 값 보존**(§10.2 발화 불변).
- origin='code_default', source_rule(원래 룰키), original_warning/critical(원본값) 메타 기록(②).
- scope='global' (국가 무관). 국가별은 rule_configs 우선(③).
- base.py 특수형(PSY 4등급 밴드·NPD overdue+7·farrowing)은 단순 w/c가 아니라 **코드 유지(㉮)**, 레지스트리 제외.

direction: 'higher_better'(낮을수록 나쁨, sev_below) / 'lower_better'(높을수록 나쁨, sev_above).
threshold 배치(§3.1): higher_better→warning_min/critical_min, lower_better→warning_max/critical_max.
"""
from __future__ import annotations

# (rule_id, kpi_code, direction, value_scale, warning, critical, source_loc)
OPERATIONAL_DEFAULTS: list[dict] = [
    # A. 공용 resolve() (23)
    dict(rule_id="batch.aiao_detect", kpi_code="BATCH_DOW_CONCENTRATION", direction="lower_better", value_scale="percent_0_100", warning=50.0, critical=70.0, src="batch.py:16"),
    dict(rule_id="boar.farrow_rate_low", kpi_code="BOAR_FARROW_RATE", direction="higher_better", value_scale="percent_0_100", warning=65.0, critical=55.0, src="boar.py:15"),
    dict(rule_id="fcr.high", kpi_code="FCR", direction="lower_better", value_scale="n/a", warning=3.0, critical=3.3, src="grow_finish.py:21"),
    dict(rule_id="adg.low", kpi_code="ADG", direction="higher_better", value_scale="n/a", warning=650.0, critical=550.0, src="grow_finish.py:44"),
    dict(rule_id="finish_mortality.high", kpi_code="FINISH_MORTALITY", direction="lower_better", value_scale="percent_0_100", warning=5.0, critical=8.0, src="grow_finish.py:67"),
    dict(rule_id="stillborn.rate_high", kpi_code="STILLBORN_RATE", direction="lower_better", value_scale="percent_0_100", warning=8.0, critical=12.0, src="litter.py:33"),
    dict(rule_id="mummified.rate_high", kpi_code="MUMMIFIED_RATE", direction="lower_better", value_scale="percent_0_100", warning=2.0, critical=4.0, src="litter.py:53"),
    dict(rule_id="born_alive.low", kpi_code="BORN_ALIVE", direction="higher_better", value_scale="n/a", warning=11.0, critical=10.0, src="litter.py:73"),
    dict(rule_id="total_born.low", kpi_code="TOTAL_BORN", direction="higher_better", value_scale="n/a", warning=12.0, critical=11.0, src="litter.py:92"),
    dict(rule_id="weaned.low", kpi_code="WEANED_COUNT", direction="higher_better", value_scale="n/a", warning=10.0, critical=9.0, src="litter.py:109"),
    dict(rule_id="birth_weight.low", kpi_code="BIRTH_WEIGHT", direction="higher_better", value_scale="n/a", warning=1.3, critical=1.1, src="litter.py:128"),
    dict(rule_id="weaning_weight.low", kpi_code="WEANING_WEIGHT", direction="higher_better", value_scale="n/a", warning=5.5, critical=5.0, src="litter.py:147"),
    dict(rule_id="lactation.too_short", kpi_code="WEANING_AGE_LOW", direction="higher_better", value_scale="n/a", warning=19.0, critical=16.0, src="litter.py:164"),
    dict(rule_id="lactation.too_long", kpi_code="WEANING_AGE_HIGH", direction="lower_better", value_scale="n/a", warning=28.0, critical=35.0, src="litter.py:180"),
    dict(rule_id="piglet.crushing_rate_high", kpi_code="CRUSHING_RATE", direction="lower_better", value_scale="percent_0_100", warning=6.0, critical=10.0, src="litter.py:197"),
    dict(rule_id="piglet.death_age_skew", kpi_code="DEATH_AGE_0_3_RATIO", direction="lower_better", value_scale="percent_0_100", warning=70.0, critical=80.0, src="litter.py:216"),
    dict(rule_id="culling.rate_high", kpi_code="CULLING_RATE", direction="lower_better", value_scale="percent_0_100", warning=45.0, critical=55.0, src="sow_herd.py:21"),
    dict(rule_id="sow_mortality.high", kpi_code="SOW_MORTALITY", direction="lower_better", value_scale="percent_0_100", warning=8.0, critical=12.0, src="sow_herd.py:44"),
    dict(rule_id="parity.high_ratio", kpi_code="HIGH_PARITY_RATIO", direction="lower_better", value_scale="percent_0_100", warning=20.0, critical=30.0, src="sow_herd.py:67"),
    dict(rule_id="replacement.rate_abnormal", kpi_code="REPLACEMENT_RATE", direction="lower_better", value_scale="percent_0_100", warning=50.0, critical=60.0, src="sow_herd.py:87"),
    dict(rule_id="parity.second_litter_slump", kpi_code="SECOND_LITTER_DROP", direction="lower_better", value_scale="n/a", warning=1.5, critical=2.5, src="sow_herd.py:111"),
    dict(rule_id="accident.parity_skew", kpi_code="ACCIDENT_P1_RATIO", direction="lower_better", value_scale="percent_0_100", warning=40.0, critical=55.0, src="sow_herd.py:129"),
    dict(rule_id="msy.below_bep", kpi_code="MSY", direction="higher_better", value_scale="n/a", warning=17.0, critical=15.0, src="sow_herd.py:151"),
    # B. reproduction.py 자체 상수 (6)
    dict(rule_id="wsi.overdue", kpi_code="WSI", direction="lower_better", value_scale="n/a", warning=10.0, critical=14.0, src="reproduction.py:16"),
    dict(rule_id="rts.rate_high", kpi_code="RTS_RATE", direction="lower_better", value_scale="percent_0_100", warning=15.0, critical=25.0, src="reproduction.py:17"),
    dict(rule_id="pwmr.high", kpi_code="PWMR", direction="lower_better", value_scale="percent_0_100", warning=15.0, critical=20.0, src="reproduction.py:18"),
    dict(rule_id="abortion.rate_high", kpi_code="ABORTION_RATE", direction="lower_better", value_scale="percent_0_100", warning=3.0, critical=5.0, src="reproduction.py:156"),
    dict(rule_id="seasonal.summer_infertility", kpi_code="SUMMER_FARROW_DROP", direction="lower_better", value_scale="n/a", warning=6.0, critical=10.0, src="reproduction.py:190"),
    dict(rule_id="conception.rate_low", kpi_code="CONCEPTION_RATE", direction="higher_better", value_scale="percent_0_100", warning=85.0, critical=80.0, src="reproduction.py:224"),
]


def to_bounds(d: dict) -> dict:
    """direction별 warning/critical → min/max 칸 배치 (§3.1)."""
    w, c = d["warning"], d["critical"]
    if d["direction"] == "higher_better":      # 값↓ 경고 → min 칸
        return dict(warning_min=w, warning_max=None, critical_min=c, critical_max=None)
    # lower_better: 값↑ 경고 → max 칸
    return dict(warning_min=None, warning_max=w, critical_min=None, critical_max=c)
