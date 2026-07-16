"""하베스트 Stage 1 manifest — 결정론·분배·조직·지역맞춤 이름 검증(§3, DB 불필요)."""
from app.harvest.manifest import (
    COUNTRY_QUOTA,
    FARM_CODES,
    ORGANIZATIONS,
    REGION_OF,
    build_manifest,
)


def test_farm_count_42():
    assert len(FARM_CODES) == 42
    assert len(set(FARM_CODES)) == 42  # 중복 없음
    assert 848 in FARM_CODES and 978 in FARM_CODES  # 추가 파일럿 농장


def test_deterministic():
    a = build_manifest()
    b = build_manifest()
    assert a == b  # 멱등: 같은 입력 → 같은 출력


def test_all_farms_assigned_country_quota():
    m = build_manifest()
    assert len(m) == 42
    counts: dict[str, int] = {}
    for row in m:
        counts[row["country_code"]] = counts.get(row["country_code"], 0) + 1
    assert counts == COUNTRY_QUOTA  # 분배 정확
    assert sum(COUNTRY_QUOTA.values()) == 42


def test_region_and_convention():
    for row in build_manifest():
        assert row["region"] == REGION_OF[row["country_code"]]
        assert row["kpi_convention_origin"] == "KR"      # 위조 0 — KPI 관례는 KR 고정
        assert row["data_classification"] == "internal_reference"


def test_organizations_grouped():
    m = {r["source_farm_ref"]: r for r in build_manifest()}
    for oid, org in ORGANIZATIONS.items():
        for f in org["farms"]:
            r = m[str(f)]
            assert r["organization_id"] == oid
            assert r["owner_type"] == "corporate"
            assert r["country_code"] == org["country"]  # 조직 농장은 조직 국가로


def test_names_locale_matched_and_present():
    for row in build_manifest():
        assert row["farm_name"] and row["owner_name"]     # 지역맞춤 합성 이름 존재
