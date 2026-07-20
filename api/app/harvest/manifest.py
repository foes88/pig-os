"""국가차등 룰엔진 하베스트 — Stage 1 manifest (설계서 v2.1 §3).

소스 KR 농장 42개를 국가/지역/조직으로 **결정론적** 배정 + 지역맞춤 합성 신원 생성.
- 위조 0: 데이터는 우리 소유(KR), 국가 '라벨'만 합성 (T1 메커니즘 검증용).
- kpi_convention_origin = KR 고정. Resolver 스코프는 country_code 사용(§11.6).
- identity_seed = hash(schema_version + manifest_version + source_system + source_farm_ref) — batch 무관 멱등(§3.2).
- Oracle 불필요: 순수 배정/명명 로직. 실제 데이터 추출은 Stage 2(P2/P3).
"""
from __future__ import annotations

import hashlib

SOURCE_SYSTEM = "pigplan"
SYNTHETIC_IDENTITY_SCHEMA_VERSION = "1"
MANIFEST_VERSION = "2026-07-16.1"
KPI_CONVENTION_ORIGIN = "KR"

# ── 소스 농장 42개 (사용자 지정: 40 + 848 + 978) ──────────────────────────────
FARM_CODES: list[int] = [
    1517, 4448, 4630, 1364, 1975, 665, 669, 2356, 3969, 1102,
    1417, 1719, 3948, 2212, 2351, 1013, 1168, 747, 657, 4636,
    4429, 1743, 4293, 1097, 2361, 1709, 88, 4365, 1888, 4227,
    1974, 4372, 1191, 1353, 1760, 4441, 2807, 4017, 4658, 4672,
    848, 978,
]

# ── 지역/국가 분배 (§3.1 비율을 42로 스케일, 합계 42) ─────────────────────────
REGION_OF = {
    "US": "US", "VN": "SEA", "PH": "SEA", "TH": "SEA", "CN": "China",
    "BR": "LatAm", "MX": "LatAm", "DE": "EU", "ES": "EU", "DK": "EU", "NL": "EU",
}
COUNTRY_QUOTA = {  # sum = 42
    "US": 10, "CN": 8, "VN": 4, "PH": 3, "TH": 3,
    "BR": 5, "MX": 3, "DE": 2, "ES": 2, "DK": 1, "NL": 1,
}
_COUNTRY_ORDER = ["US", "CN", "VN", "PH", "TH", "BR", "MX", "DE", "ES", "DK", "NL"]

# ── 조직(§3.1: 2 organization × 2~3 farm) — 리스트의 자연 회사그룹 활용 ─────────
ORGANIZATIONS = {
    "ORG_DABI": {
        "name": "Dabi Genetics (harvest)", "type": "producer_group",
        "country": "US", "farms": [665, 669, 747],
    },
    "ORG_WISE": {
        "name": "WiseLake Group (harvest)", "type": "integrator",
        "country": "CN", "farms": [4630, 3948, 1013],
    },
}
_ORG_FARM_TO_ID = {f: oid for oid, o in ORGANIZATIONS.items() for f in o["farms"]}

# ── 국가별 합성 이름 풀 (지역맞춤). farm/owner 각각, 결정론적 선택 ──────────────
_FARM_POOL = {
    "US": ["Prairie Ridge Farm", "Cornbelt Swine Co", "Heartland Hog Farm", "Redwood Pork", "Liberty Sow Unit", "Great Plains Piggery", "Maple Creek Farm", "Sunset Valley Pork", "Iron Gate Swine", "Blue River Hog Co"],
    "CN": ["金猪养殖场", "丰农种猪场", "牧原示范场", "东方生猪养殖", "绿源猪场", "宏图养殖场", "旭日种猪", "润泽猪业", "天成养殖", "华兴猪场"],
    "VN": ["Trại heo Phú Thịnh", "Trang trại Đồng Tâm", "Heo giống Minh Phát", "Trại Tân Nông", "Chăn nuôi Hưng Phú", "Trang trại Bình An", "Trại heo Đại Lộc", "Nông trại Sông Xanh"],
    "PH": ["Bagong Silang Farm", "Golden Pig Piggery", "Masaganang Hog Farm", "Sunrise Swine Ph", "Kanlaon Pork Farm", "Bayanihan Piggery"],
    "TH": ["ฟาร์มสุกรรุ่งเรือง", "ฟาร์มหมูทองคำ", "ฟาร์มเกษตรพัฒนา", "สุกรฟาร์มบ้านสวน", "ฟาร์มหมูสยาม", "ฟาร์มไทยเจริญ"],
    "BR": ["Granja Santa Rita", "Suínos Vale Verde", "Granja Boa Vista", "Fazenda Porto Alegre", "Granja Serra Azul", "Suinocultura Ipê", "Granja São José"],
    "MX": ["Granja Los Encinos", "Porcícola El Roble", "Granja Santa Fe", "Cerdos del Bajío", "Granja La Esperanza"],
    "DE": ["Sauenhof Meierberg", "Schweinegut Lindenhof", "Ferkelhof Rheinau"],
    "ES": ["Granja Los Olivos", "Porcino Valdés", "Granja El Encinar"],
    "DK": ["Søndergård Svin"],
    "NL": ["Zeugenhof De Peel"],
}
_OWNER_POOL = {
    "US": ["John Miller", "Robert Hayes", "William Carter", "James Bennett", "David Cole", "Michael Ross", "Thomas Reed", "Daniel Ford", "Paul Grant", "Kevin Shaw"],
    "CN": ["王建国", "李国强", "张伟", "刘志明", "陈国华", "赵永军", "孙立新", "周德福", "吴敬业", "徐海涛"],
    "VN": ["Nguyễn Văn Phú", "Trần Đình Tâm", "Lê Minh Phát", "Phạm Quốc Nông", "Hoàng Hưng Phú", "Vũ Bình An", "Đặng Đại Lộc", "Bùi Sông Xanh"],
    "PH": ["Jose Reyes", "Antonio Cruz", "Ramon Santos", "Ricardo Bautista", "Manuel Aquino", "Eduardo Villar"],
    "TH": ["สมชาย รุ่งเรือง", "วิชัย ทองคำ", "ประเสริฐ เกษตร", "สุรพงษ์ บ้านสวน", "อนุชา สยาม", "ธนา เจริญ"],
    "BR": ["João Silva", "Carlos Souza", "Pedro Almeida", "Marcos Oliveira", "Antônio Costa", "Luiz Pereira", "José Santos"],
    "MX": ["Juan Hernández", "Miguel Robles", "Alejandro Vega", "Ricardo Bajío", "Fernando López"],
    "DE": ["Hans Meier", "Klaus Lindner", "Werner Rhein"],
    "ES": ["Antonio Valdés", "Miguel Olivares", "José Encinar"],
    "DK": ["Lars Sønder"],
    "NL": ["Jan de Vries"],
}


def _seed(source_farm_ref: int | str) -> int:
    raw = f"{SYNTHETIC_IDENTITY_SCHEMA_VERSION}:{MANIFEST_VERSION}:{SOURCE_SYSTEM}:{source_farm_ref}"
    return int(hashlib.md5(raw.encode()).hexdigest(), 16)


def _pick(pool: list[str], seed: int) -> str:
    return pool[seed % len(pool)]


def _assign_countries() -> dict[int, str]:
    """개별농가를 quota 슬롯에 **시드 랜덤**으로 배정(조직농가는 조직 국가 고정).

    - 각국 나라별로 골고루 분포(quota 유지) + 정렬순 편중 제거를 위해 셔플 사용.
    - MANIFEST_VERSION 시드 → 멱등(재실행 동일). farm_code로 매핑 재현 가능.
    """
    import random
    rng = random.Random(f"{MANIFEST_VERSION}:{SOURCE_SYSTEM}:country")
    assigned: dict[int, str] = {}
    remaining_quota = dict(COUNTRY_QUOTA)
    # 1) 조직 농가 먼저 — 조직 지정 국가
    for oid, org in ORGANIZATIONS.items():
        for f in org["farms"]:
            assigned[f] = org["country"]
            remaining_quota[org["country"]] -= 1
    # 2) 나머지: 남은 quota를 슬롯 풀로 펼쳐 셔플 → 농가에 랜덤 배정(분포는 quota로 균형)
    slots = [cc for cc in _COUNTRY_ORDER for _ in range(remaining_quota.get(cc, 0))]
    rng.shuffle(slots)
    individuals = sorted(f for f in FARM_CODES if f not in assigned)
    rng.shuffle(individuals)
    for f, cc in zip(individuals, slots, strict=True):
        assigned[f] = cc
    return assigned


def build_manifest() -> list[dict]:
    """42농장 → {source_farm_ref, country_code, region, organization_id, owner_type,
    farm_name, owner_name, data_origin, kpi_convention_origin} 결정론 리스트."""
    countries = _assign_countries()
    out: list[dict] = []
    for f in FARM_CODES:
        cc = countries[f]
        s = _seed(f)
        org_id = _ORG_FARM_TO_ID.get(f)
        out.append({
            "source_system": SOURCE_SYSTEM,
            "source_farm_ref": str(f),
            "country_code": cc,
            "region": REGION_OF[cc],
            "organization_id": org_id,
            "owner_type": "corporate" if org_id else "individual",
            "farm_name": _pick(_FARM_POOL[cc], s),
            "owner_name": _pick(_OWNER_POOL[cc], s >> 8),
            "data_origin": "pigplan_migration",
            "kpi_convention_origin": KPI_CONVENTION_ORIGIN,
            "data_classification": "internal_reference",
        })
    return out
