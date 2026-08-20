"""BR Pilot v1 seed 게이트 (G1~G4).

정본: docs/product/COUNTRY_PRODUCT_SPEC_BR.md v0.3
시드 SSOT: app/db/br_pilot_seed.py

핵심 원칙(OPTION A): UI visibility 는 정책 데이터가 결정한다.
프론트 레지스트리에 우연히 없어서 안 보이는 것은 결정이 아니다.
"""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.br_pilot_seed import (
    BR_PILOT_HIDDEN,
    BR_PILOT_VISIBLE,
    COUNTRY,
    HEADLINE_KPI,
    VISIBLE_CODES,
    policy_rows,
    presentation_rows,
)
from app.db.models.kpi_policy import CountryKpiPolicy
from app.db.models.kpi_presentation import CountryKpiPresentation
from app.services.kpi_policy_resolver import (
    pick_headline,
    resolve_display_kpis,
    resolve_kpi_presentation,
)

pytestmark = pytest.mark.anyio

# GLOBAL seed(마이그레이션 c7d9e1f3a5b8)와 동일한 14개. 테스트 DB 는 create_all 이라
# 마이그레이션 시드가 없으므로 여기서 동일하게 재현한다.
GLOBAL_SEED = (
    ("PSY", "PRIMARY"), ("NPD", "PRIMARY"), ("FARROWING_RATE", "PRIMARY"),
    ("SOW_TURNOVER", "SECONDARY"), ("MSY", "SECONDARY"), ("FCR", "SECONDARY"),
    ("ADG", "SECONDARY"), ("WSI", "SECONDARY"), ("RTS_RATE", "SECONDARY"),
    ("PWMR", "SECONDARY"), ("BORN_ALIVE", "SECONDARY"), ("WEANED_COUNT", "SECONDARY"),
    ("SOW_MORTALITY", "SECONDARY"), ("STILLBORN_RATE", "SECONDARY"),
)


async def _seed(db: AsyncSession, *, extra_global: tuple[str, ...] = ()) -> None:
    """GLOBAL 14 + BR Pilot 시드를 넣는다. extra_global 로 신규 GLOBAL KPI 를 모사."""
    for code, role in GLOBAL_SEED + tuple((c, "SECONDARY") for c in extra_global):
        db.add(CountryKpiPolicy(
            scope_level="GLOBAL", kpi_code=code, compute_enabled=True, display_role=role,
            rule_enabled=False, benchmark_exposure="CONTEXT_ONLY", prediction_feature=False,
            api_export_policy="TENANT_ONLY", decision_status="APPROVED", decided_by="test",
        ))
    for r in policy_rows():
        db.add(CountryKpiPolicy(id=uuid.uuid4(), **r))
    for r in presentation_rows():
        db.add(CountryKpiPresentation(id=uuid.uuid4(), **r))
    await db.flush()


# ── G1 ────────────────────────────────────────────────────────────────────────

async def test_g1_resolved_set_matches_spec(db: AsyncSession):
    """G1: BR 이 표시하는 KPI 집합이 Spec v0.3 의 Pilot subset 과 정확히 일치."""
    await _seed(db)
    got = {r.kpi_code for r in await resolve_display_kpis(db, country=COUNTRY)}
    assert got == VISIBLE_CODES == {"PSY", "FARROWING_RATE", "NPD"}


# ── G2 ────────────────────────────────────────────────────────────────────────

async def test_g2_visible_count_is_exactly_three(db: AsyncSession):
    """G2: 개수 고정. 부분집합만 검사하면 카드가 늘어난 경우를 못 잡는다."""
    await _seed(db)
    assert len(await resolve_display_kpis(db, country=COUNTRY)) == 3


async def test_g2_other_country_still_sees_global_set(db: AsyncSession):
    """BR 의 HIDDEN 은 BR 에만 적용된다 — 다른 국가는 GLOBAL 14개 그대로."""
    await _seed(db)
    assert len(await resolve_display_kpis(db, country="US")) == len(GLOBAL_SEED)


# ── G3 ────────────────────────────────────────────────────────────────────────

async def test_g3_headline_is_psy(db: AsyncSession):
    """G3: 성공 기준 2번(PSY 가 headline)의 자동 검증."""
    await _seed(db)
    rows = await resolve_display_kpis(db, country=COUNTRY)
    assert pick_headline(rows) == HEADLINE_KPI == "PSY"
    assert rows[0].kpi_code == "PSY", "headline 은 항상 첫 항목"


async def test_g3_order_and_local_labels_match_spec(db: AsyncSession):
    """순서·현지 명칭이 Spec 확정값과 일치(성공 기준 3·4번)."""
    await _seed(db)
    rows = await resolve_display_kpis(db, country=COUNTRY)
    assert [r.kpi_code for r in rows] == [c for c, _, _ in BR_PILOT_VISIBLE]
    assert [r.local_label for r in rows] == [lbl for _, _, lbl in BR_PILOT_VISIBLE]
    assert [r.display_order for r in rows] == [o for _, o, _ in BR_PILOT_VISIBLE]


# ── G4 ────────────────────────────────────────────────────────────────────────

async def test_g4_every_global_kpi_has_an_explicit_br_decision(db: AsyncSession):
    """★ G4: GLOBAL 에 KPI 가 추가돼도 BR visible set 이 조용히 늘 수 없다.

    리졸버에 COUNTRY default-deny 를 넣는 대신 coverage 로 강제한다
    (default-deny 는 GLOBAL→COUNTRY 상속 설계를 뒤집고 미시드 국가 화면을 비운다).
    GLOBAL 에 KPI 를 추가하고 BR 결정을 빠뜨리면 이 테스트가 실패한다 = 결정 강제.
    """
    await _seed(db)
    global_codes = {c for c, _ in GLOBAL_SEED}
    decided = VISIBLE_CODES | set(BR_PILOT_HIDDEN)
    missing = global_codes - decided
    assert not missing, (
        f"GLOBAL 에 있는데 BR 결정이 없는 KPI: {sorted(missing)} — "
        "COUNTRY_PRODUCT_SPEC_BR.md 를 개정하고 br_pilot_seed.py 에 visible/HIDDEN 을 명시하십시오"
    )
    assert not (decided - global_codes), "BR 에 결정은 있는데 GLOBAL 에 없는 KPI(오타 가능)"


async def test_g4_new_global_kpi_without_br_decision_is_detected(db: AsyncSession):
    """신규 GLOBAL KPI 가 결정 없이 들어오면 실제로 BR 목록이 늘어난다는 사실을 고정.

    이 테스트는 '누수가 가능하다'는 사실 자체를 문서화한다 — 그래서 위 coverage
    게이트가 필요하다. 누수를 허용하는 게 아니라, 게이트가 없으면 어떻게 되는지를 못 박는다.
    """
    await _seed(db, extra_global=("NEW_KPI_X",))
    rows = await resolve_display_kpis(db, country=COUNTRY)
    assert {r.kpi_code for r in rows} == VISIBLE_CODES | {"NEW_KPI_X"}
    # 그리고 coverage 게이트가 이 상황을 잡아낸다
    assert "NEW_KPI_X" not in (VISIBLE_CODES | set(BR_PILOT_HIDDEN))


# ── 회귀: HIDDEN 은 표현 행이 없어도 확실히 숨는다 ────────────────────────────

async def test_hidden_kpi_has_no_presentation_row_and_stays_hidden(db: AsyncSession):
    """SOW_TURNOVER: BR 에서 HIDDEN + 현지명 UNVERIFIED → 표현 행 자체가 없다."""
    await _seed(db)
    assert "SOW_TURNOVER" not in {r.kpi_code for r in await resolve_display_kpis(db, country=COUNTRY)}
    pres = await resolve_kpi_presentation(db, kpi_code="SOW_TURNOVER", country=COUNTRY)
    assert pres.local_label is None, "확정되지 않은 현지명을 넣지 않는다"
    assert pres.display_order is None


async def test_seed_module_matches_spec_document(db: AsyncSession):
    """시드 모듈과 정본 문서가 같은 말을 하는지 — 문서의 표를 파싱해 대조."""
    import re
    from pathlib import Path

    doc = Path("../docs/product/COUNTRY_PRODUCT_SPEC_BR.md").read_text(encoding="utf-8")
    section = doc.split("## 2. BR Pilot v1")[1].split("### 2.1")[0]
    codes = re.findall(r"`([A-Z_]+)`", section)
    assert set(codes) == VISIBLE_CODES, (
        f"문서 §2 표({sorted(set(codes))})와 br_pilot_seed.py({sorted(VISIBLE_CODES)}) 불일치"
    )
    for _code, _order, label in BR_PILOT_VISIBLE:
        assert label in section, f"현지명 '{label}' 이 문서 §2 에 없음"
