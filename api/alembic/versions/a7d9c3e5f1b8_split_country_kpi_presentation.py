"""Presentation Policy 분리 — country_kpi_presentation 신설 + CKP.display_order 이관

CKP  = 그 KPI 를 써도 되는가 / 어느 군인가   (거버넌스)
CKPRES = 그 KPI 를 뭐라 부르고 몇 번째인가   (표현)

10505d3(CKP.display_order 추가)을 revert 하지 않고 migration 으로 이관한다.
데이터 COPY 는 결과가 0건이어도 항상 실행한다(환경별 seed 차이를 가정하지 않음).

Revision ID: a7d9c3e5f1b8
Revises: f2b4d6a8c1e5
"""
import sqlalchemy as sa

from alembic import op

revision = "a7d9c3e5f1b8"
down_revision = "f2b4d6a8c1e5"
branch_labels = None
depends_on = None

# GLOBAL 스코프는 country_code/farm_type/tenant_id 가 전부 NULL 이라 평범한 UNIQUE 로는
# 중복이 막히지 않는다(NULL != NULL). COALESCE 함수 인덱스로 실제 유일성을 강제한다.
_UQ = """
CREATE UNIQUE INDEX uq_ckpres_scope_kpi ON country_kpi_presentation (
    scope_level,
    COALESCE(country_code, ''),
    COALESCE(farm_type, ''),
    COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid),
    kpi_code
)
"""

# 이관: CKP 는 production_stage/herd_size_band 축이 더 있어 같은 (scope,kpi) 가 복수일 수 있다.
# Presentation 은 그 축이 없으므로 최신 effective_from 1건만 승격한다.
_COPY = """
INSERT INTO country_kpi_presentation (
    id, scope_level, country_code, farm_type, tenant_id, kpi_code,
    display_order, display_order_override, local_label,
    effective_from, effective_to, decision_status, note
)
SELECT DISTINCT ON (scope_level, country_code, farm_type, tenant_id, kpi_code)
    gen_random_uuid(), scope_level, country_code, farm_type, tenant_id, kpi_code,
    display_order,
    TRUE,                       -- 이관값은 명시 지정이었으므로 override
    NULL,
    effective_from, effective_to,
    CASE WHEN decision_status = 'APPROVED' THEN 'APPROVED' ELSE 'PROPOSED' END,
    'migrated from country_kpi_policy.display_order (a7d9c3e5f1b8)'
FROM country_kpi_policy
WHERE display_order IS NOT NULL
ORDER BY scope_level, country_code, farm_type, tenant_id, kpi_code, effective_from DESC
"""


def upgrade() -> None:
    op.create_table(
        "country_kpi_presentation",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("scope_level", sa.String(16), nullable=False),
        sa.Column("country_code", sa.String(2)),
        sa.Column("farm_type", sa.String(24)),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("kpi_code", sa.String(64), nullable=False),
        sa.Column("display_order", sa.Integer()),
        sa.Column("display_order_override", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("local_label", sa.String(128)),
        sa.Column("effective_from", sa.Date()),
        sa.Column("effective_to", sa.Date()),
        sa.Column("decision_status", sa.String(16), nullable=False,
                  server_default=sa.text("'PROPOSED'")),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        # ★ country_kpi_policy.ck_ckp_scope_keys 원문 복제 — 새로 쓰지 않는다.
        sa.CheckConstraint(
            "(scope_level = 'GLOBAL'    AND country_code IS NULL AND farm_type IS NULL AND tenant_id IS NULL) OR "
            "(scope_level = 'COUNTRY'   AND country_code IS NOT NULL AND farm_type IS NULL AND tenant_id IS NULL) OR "
            "(scope_level = 'FARM_TYPE' AND country_code IS NOT NULL AND farm_type IS NOT NULL AND tenant_id IS NULL) OR "
            "(scope_level = 'TENANT'    AND tenant_id IS NOT NULL)",
            name="ck_ckpres_scope_keys",
        ),
        sa.CheckConstraint("scope_level IN ('GLOBAL', 'COUNTRY', 'FARM_TYPE', 'TENANT')",
                           name="ck_ckpres_scope"),
        sa.CheckConstraint("display_order IS NULL OR display_order >= 0", name="ck_ckpres_order"),
        sa.CheckConstraint("decision_status IN ('PROPOSED', 'APPROVED')", name="ck_ckpres_status"),
    )
    op.create_index("ix_ckpres_lookup", "country_kpi_presentation", ["country_code", "kpi_code"])
    op.execute(_UQ)

    # 데이터 이관 — 항상 실행. 이관 후 유실 0 을 같은 트랜잭션에서 검증한다.
    op.execute(_COPY)
    src = op.get_bind().execute(sa.text(
        "SELECT count(*) FROM (SELECT DISTINCT scope_level, country_code, farm_type, tenant_id,"
        " kpi_code FROM country_kpi_policy WHERE display_order IS NOT NULL) s"
    )).scalar_one()
    dst = op.get_bind().execute(sa.text(
        "SELECT count(*) FROM country_kpi_presentation WHERE display_order_override"
    )).scalar_one()
    if dst < src:
        raise RuntimeError(f"display_order 이관 유실: CKP {src}건 → presentation {dst}건")

    op.drop_column("country_kpi_policy", "display_order")


def downgrade() -> None:
    op.add_column("country_kpi_policy", sa.Column("display_order", sa.Integer()))
    op.execute("""
        UPDATE country_kpi_policy p
           SET display_order = r.display_order
          FROM country_kpi_presentation r
         WHERE r.display_order_override
           AND r.kpi_code = p.kpi_code
           AND r.scope_level = p.scope_level
           AND r.country_code IS NOT DISTINCT FROM p.country_code
           AND r.farm_type IS NOT DISTINCT FROM p.farm_type
           AND r.tenant_id IS NOT DISTINCT FROM p.tenant_id
    """)
    op.drop_index("uq_ckpres_scope_kpi", table_name="country_kpi_presentation")
    op.drop_index("ix_ckpres_lookup", table_name="country_kpi_presentation")
    op.drop_table("country_kpi_presentation")
