"""GLOBAL 을 최소 안전값 3개로 축소 — 미결정 국가 자동 노출 차단 (K-01-1 A)

GLOBAL seed(c7d9e1f3a5b8)가 14개를 전부 visible 로 뒀는데, 그건 "현재 라이브 동작
codify" 였지 국가별 표시 결정이 아니었다. 화면에 4장만 나오던 건 프론트가 그만큼만
그릴 수 있어서였다 — 정책이 아니라 구현 한계다.

metrics 맵 노출(1d07768)로 그 한계가 사라지면서, 결정한 적 없는 지표가 프로덕션
11개국(US·CN·KR·MX·VN·PH·TH·DE·ES·DK·NL)에 자동으로 노출되는 상태가 됐다.
GLOBAL 을 default-deny 로 재정의해 그 경로를 막는다.

★ 운영 영향: SOW_TURNOVER 카드가 사라진다(현재 4장 → 3장). "화면 변화 0" 이 아니라
  "결정 없는 노출 확대 0" 이다. 되살리려면 국가별 명시 승인으로 COUNTRY 에서 켠다.
★ compute_enabled 는 건드리지 않는다 — 계산·룰 판정은 그대로, 표시만 숨긴다.

시드 값 SSOT: app/db/global_policy_defaults.py

Revision ID: d1a4c6e8b2f5
Revises: c9f3e5a7b1d4
"""
import sqlalchemy as sa

from alembic import op
from app.db.global_policy_defaults import GLOBAL_HIDDEN, GLOBAL_VISIBLE

revision = "d1a4c6e8b2f5"
down_revision = "c9f3e5a7b1d4"
branch_labels = None
depends_on = None

_SQL = sa.text(
    "UPDATE country_kpi_policy SET display_role = :role "
    "WHERE scope_level = 'GLOBAL' AND kpi_code = ANY(:codes)"
).bindparams(sa.bindparam("codes", type_=sa.ARRAY(sa.String)))


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(_SQL, {"role": "HIDDEN", "codes": list(GLOBAL_HIDDEN)})

    # 축소 후 GLOBAL visible 이 정확히 3개인지 같은 트랜잭션에서 확인한다.
    got = set(bind.execute(sa.text(
        "SELECT kpi_code FROM country_kpi_policy WHERE scope_level = 'GLOBAL' "
        "AND display_role IN ('PRIMARY','SECONDARY') AND decision_status = 'APPROVED'"
    )).scalars().all())
    if got != set(GLOBAL_VISIBLE):
        raise RuntimeError(
            f"GLOBAL visible 이 기대와 다름: {sorted(got)} != {sorted(GLOBAL_VISIBLE)}")


def downgrade() -> None:
    # 되돌리면 원래 seed 의 SECONDARY 로 복원(전부 다시 보이게 된다).
    op.get_bind().execute(_SQL, {"role": "SECONDARY", "codes": list(GLOBAL_HIDDEN)})
