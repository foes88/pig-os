# 작업 A 출력 — KPI Governance v3.1 schema migration + seed validator

> 기준: handoff/KPI_GOVERNANCE_v3.1.md / PROMPT_A_schema_migration.md
> 실행일: 2026-06-25 / 실행 환경: 활성 dev PC (c:\dev\PigOS), dev DB(pigos, Docker PostgreSQL 16)
> 범위: schema migration + seed validator + 테스트 15종 + KR 27 안전 이전. **KR verified 확정은 작업 B.**

---

## 1. 생성/수정 파일

| 파일 | 내용 |
|---|---|
| `handoff/KPI_GOVERNANCE_v3.1.md` | 기준 문서(단일 진실 소스) 보존 |
| `api/app/db/models/benchmark.py` | 모델 3종 + DB 제약(★④⑦⑧⑫ CHECK·복합FK·active verified unique) |
| `api/app/db/benchmark_seed.py` | §2 KPI_DEFINITIONS 16종 + `validate_benchmark()` seed validator(★⑦⑧⑫+§6) |
| `api/app/engine/benchmark_thresholds.py` | threshold 방향 해석(★⑪)·발화 게이팅(★③)·UI배지 |
| `api/alembic/versions/c5e7a9b1d3f0_kpi_governance_v31_3table.py` | 마이그레이션(테이블→시드→KR이전→제약강화) |
| `api/app/db/models/__init__.py` | 모델 등록 |
| `api/tests/integration/test_benchmark_governance.py` | 테스트 15종 + 정상통과 1 |

기존 동작 변경: **없음**. `default_metric_values`(KR 27 원본)·Rule Engine 미수정. 3-테이블은 거버넌스 계층으로 추가만. Rule Engine 연결은 B 이후 별도 단계.

---

## 2. 3-테이블 DDL (적용본 = 문서 §3.1~3.3 + §3.5)
- `kpi_definitions` (PK: kpi_code+definition_id) — direction/denominator_type/period_basis/value_scale CHECK. value_scale NOT NULL.
- `source_observations` (PK: obs_id) — obs_group_id, period_start/end/publication_date(★⑨), raw_fields_json(★⑩).
- `benchmarks` (PK: bench_id) — warning/critical min/max(★①), value_scale(★⑥), mapping/comparison/benchmark_status CHECK(★③), 복합FK(★④), ★⑦⑧⑫ CHECK, active-verified 부분 unique index, is_active/effective_from/to(이력).
  - **value_scale 보완**: benchmarks도 `n/a` 허용(kpi_definitions와 동일 집합). count KPI(PSY/NPD 등 n/a)가 NULL이면 can_fire가 막아 발화 불가해지므로. ★⑫-4(value_scale 일치) 깔끔히 성립.

## 3. kpi_definitions 시드 결과
- **16종 시드** (§2.1 higher 7 + §2.2 lower 8 + §2.3 range 1).
- **direction 누락 0 / value_scale 누락 0** (검증 통과).
- definition_id 규칙: `PIGOS_<KPI>_V1`.

## 4. KR 27종 이전 결과표 (강등 = 안전 이전, verified 0 — B에서 판정)

| KR metric | → kpi_code | 이전 위치 | 판정상태 | 강등 | 사유 |
|---|---|---|---|---|---|
| PSY | psy | src_obs + benchmarks | provisional | ↓ | 모집단/기간/정의 미확정(higher: warning_min22/critical_min18/target24) |
| MSY | msy | src_obs + benchmarks | provisional | ↓ | KR 임계 없음, target26만 |
| FARROWING_RATE | farrowing_rate | src_obs + benchmarks | provisional | ↓ | higher: warning_min83/critical_min78/target85, percent |
| WEANED_COUNT | weaned_per_litter | src_obs + benchmarks | provisional | ↓ | higher: warning_min10/critical_min9/target11 |
| NPD | npd | src_obs + benchmarks | provisional | ↓ | lower: warning_max35/critical_max50 |
| SOW_MORTALITY | sow_mortality | src_obs + benchmarks | provisional | ↓ | lower: warning_max10, percent |
| WSI | wsi | src_obs + benchmarks | provisional | ↓ | lower: warning_max7/critical_max10 |
| FCR | fcr | src_obs + benchmarks | provisional | ↓ | lower: warning_max3/critical_max3.2 (value_scale=n/a, **D-13**) |
| PRE_WEANING_MORTALITY | prewean_mortality | src_obs + benchmarks | provisional | ↓ | lower: warning_max10/critical_max14, percent |
| CULLING_RATE | culling_rate | src_obs + benchmarks | provisional | ↓ | range_target이나 KR 상단 임계만(warning_max50/target40), 하단 없음 |
| **STILLBORN_RATE** | stillbirth_rate | src_obs + benchmarks | **missing** | ↓↓ | PigOS=(사산+미라)/총산. KR 분자 미라포함 불명·원자료 분리 없어 재정규화 불가 |
| ABORTION_RATE | — | **src_obs만** | (정의없음) | — | §2에 KPI 없음 |
| BORN_ALIVE | — | src_obs만 | (정의없음) | — | §2에 KPI 없음(복당총산 미정의) |
| HIGH_PARITY_RATIO | — | src_obs만 | (정의없음) | — | §2에 KPI 없음 |
| MARKET_PRICE_HEAD | — | src_obs만 | (정의없음) | — | 가격(비KPI) |
| RTS_RATE | — | src_obs만 | (정의없음) | — | §2에 KPI 없음 |
| SOW_RESIDUAL_P0~P6 (7) | — | src_obs만 | (정의없음) | — | 잔존가(비KPI) |
| SOW_SALVAGE_CULL/DEATH (2) | — | src_obs만 | (정의없음) | — | 잔존가(비KPI) |
| WEANING_AGE_LOW | — | src_obs만 | (정의없음) | — | §2에 KPI 없음 |
| WEANING_WEIGHT | — | src_obs만 | (정의없음) | — | §2에 KPI 없음 |

**집계**: source_observations 27행(전부 보존) / benchmarks 11행(provisional 10 + missing 1) / orphan 16(src_obs만, 복합FK 대상 KPI 없음). **verified 0건**(전부 B 대기).

## 5. 테스트 결과 (15종 + 1)

| # | 테스트 | 결과 |
|---|---|---|
| 1 | lower_better 값↑→severity↑ | PASS |
| 2 | higher_better 값↓→severity↑ | PASS |
| 3 | range_target 양방향 | PASS |
| 4 | incompatible/unknown→insight 금지 | PASS |
| 5 | benchmark_status 5종 UI 배지 | PASS |
| 6 | normalized_verified인데 formula 없음→실패 | PASS |
| 7 | (kpi,def) 불일치 복합FK 실패(DB) | PASS |
| 8 | value_scale 혼용 비교 차단 | PASS |
| 9 | verified인데 is_provisional=true→실패(★⑦) | PASS |
| 10 | normalized_verified 6조건 누락→실패(★⑧) | PASS |
| 11 | 방향별 칸 읽기(★⑪) | PASS |
| 12 | value_scale≠kpi_def→실패(★⑫-4) | PASS |
| 13 | transformed_value 있는데 missing→실패(★⑫-5) | PASS |
| 14 | incompatible인데 발화가능→실패(★⑫-6) | PASS |
| 15 | active verified 중복→차단(DB unique) | PASS |
| + | 정상 provisional 통과(역검증) | PASS |

**전체 회귀: pytest 504 passed** (기존 488 + 신규 16).

## 6. migration 순서 준수 확인
- ① 3-테이블 생성(컬럼/PK/enum CHECK만) → ② kpi_definitions 16 시드 → ③ KR 27 이전(강등) → ④ 복합FK·★⑦⑧⑫ CHECK·active-verified unique **데이터 이전 후 ALTER**.
- 제약을 먼저 걸어 기존 데이터로 migration이 터지는 일 없음(upgrade 1회 성공). enum-domain CHECK만 inline(이전 데이터가 유효 enum을 provably 충족 — 무해).
- KR 27 원본(default_metric_values) **삭제 0**.

## 7. 작업 B 인계 목록
- **provisional 10종**(psy/msy/farrowing_rate/weaned_per_litter/npd/sow_mortality/wsi/fcr/prewean_mortality/culling_rate): 한돈팜스 공식 PDF(D-6)로 모집단·기간·정의 확정 → verified 판정. 현재 comparison_status=compatible/mapping_status=exact는 **잠정**(B가 재확인).
- **missing 1종**(stillbirth_rate): 한돈팜스 원문에서 사산/미라 분리 확인 → 분리되면 normalized_verified(transform_formula 기록), 안되면 missing 유지.
- **orphan 16종**: §2에 없는 KPI(가격/잔존가/RTS/고산차/이유체중/이유일령/유산율/생존산자수). KPI 정의 추가 여부 결정 필요(D 후속).
- **culling_rate**: range_target 하단(노령화) 기준 미확보 — KR은 상단만.
- US PigCHAMP(§4.3) 적재는 작업 후속(6단계): 사산율 normalized_verified / 분만율 verified / PWMFY missing.

## 8. 발견된 결정 질문
- **D-13 (신규)**: 문서 §2.2는 `fcr value_scale='ratio'`이나 §3.1/§4.3 허용 enum은 `percent_0_100|ratio_0_1|n/a`뿐. FCR(≈2.5)은 percent도 0~1 ratio도 아니므로 **`n/a`로 잠정 시드**(enum-safe). → 사용자 확정 필요. `benchmark_seed.py _FCR_VALUE_SCALE` 한 곳 수정.
- **D-6/D-7/D-8** (문서 미해결, 토론 불가): D-6 한돈팜스 PDF / D-7 KR전용 발화룰 여부 / D-8 validator 7 vs 8 — 1차자료·코드확인 필요(작업 A 범위 밖).
- period_basis가 §2.2/§2.3에 명시 없어 denominator_type 기준 추론(avg_inventory_sow→rolling_365, 그 외→period). 문서 §2.1 패턴 따름 — B에서 확인 권장.

## 9. 운영 배포
- **미배포**(dev만 적용). 추가 테이블 + KR copy로 무해·additive지만, 운영 DB 변경은 사용자 확인 후. Rule Engine 연결(발화) 전이라 배포 급하지 않음 — 작업 B(verified 판정) 후 함께 배포 권장.
