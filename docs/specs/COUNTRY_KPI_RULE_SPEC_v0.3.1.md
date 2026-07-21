# COUNTRY_KPI_RULE_SPEC v0.3.1
## 국가별 KPI·룰 엔진 및 경영 KPI 기술 스펙 — 상속·lineage·런타임 게이트 패치

> **문서 정의**: PigOS 전체 기획서가 아니다. 국가별 KPI 정책, 룰 엔진 계층, 경영 KPI 도메인의 기술 스펙. 제품·BM·데이터 권리·PigSignal 상품화는 `docs/PIGOS_SPEC_INDEX.md` 참조.
> **상태**: DRAFT — 미확정. 승인 전까지 코드 반영 금지.
> **v0.3 → v0.3.1 변경 요약**: §4 상속 스키마 수정(설계 버그), §4.7 override 방향 규칙, §4.8 예외 정책, §4.9 데이터 원산지 분리, §14.1 런타임 오픈 게이트, §15 최소 이벤트 envelope 신설, §6.3 보안·보존 블로커(B-08), 테스트 추가.
> **연관 SSOT**: KPI_GOVERNANCE_v3.2 · 30농가 이관 스펙 SSOT v2.1 · Safe Claim Matrix v0.4 · BILLING_ARCHITECTURE_NOTE.md · docs/PIGOS_SPEC_INDEX.md · docs/specs/ANONYMIZATION_RELEASE_GATE_SPEC.md · docs/specs/2026-06-17_country-kpi-differences.md (기존 국가 KPI 분석 — v0.4 실사 시 대조 필수)

---

## 0. 문서 규칙

### 0.1 위조 0 — 수치와 결정 모두

- 미확인 수치 기입 금지: `TBD` / `MISSING`.
- 미승인 결정을 확정으로 기술 금지: `PROPOSED` → Decision Register에서만 `APPROVED` 승격.
- 벤치마크·임계 수치에 `source / year / cohort / denominator` 병기.
- 예시 코드의 수치는 `null` 또는 플레이스홀더.

### 0.2 상태 어휘

`APPROVED` / `PROPOSED` / `REVIEWED` / `TBD` / `MISSING` / `BLOCKED(B-xx)` / `EXCLUDED` / `DEFERRED`

---

## 1. 배경 (2026-07-21 회의) — 제안과 확정의 구분

### 1.1 확정 (기존 SSOT)
2-리졸버 구조(발화·색상 = Threshold Resolver 단독, Benchmark Context = 맥락만) · 프론트 zero override · `internal_reference` fail-closed · A-rule · 사산율 공식과 외부 비교 무효.

### 1.2 회의 제안 (PROPOSED)

| 제안 | Register |
|---|---|
| 무료 Core 사육 두수 무제한 | D-08 |
| 경영관리 = 제품 기능 P0 | D-09 |
| US/BR: MSY 전면, PSY 보조 | §4.6 decision_status=PROPOSED |
| R1 무료 / R2 유료 경계 | D-10 (Entitlement Matrix와 일괄) |

---

## 2. 아키텍처 개요

```
입력 이벤트 ─▶ [Canonical Event Envelope (§15) 정규화]
             ─▶ [L1 Policy Gate: resolved_country_kpi_policy 해석 (§4)]
                  ├─ compute_enabled=false ──▶ 종료 (무평가·무로그)
                  └─ compute_enabled=true
                        ├─ rule_enabled ──────▶ R1 Threshold Resolver (무료)
                        ├─ benchmark_exposure ▶ C1 Benchmark Context (무료, verdict 금지)
                        │     └─ [Data Asset Policy 확인 (§4.9): 원산지별 사용 가능 범위]
                        └─ prediction_feature ▶ R2 Prediction Pipeline (유료)
                              └─ entitlement 게이팅 = 알림 "생성" 시점
```

불변 원칙 유지: R1 단독 발화 권한 / C1 verdict 금지 / 프론트 zero override / 무료 테넌트 DB에 R2 알림 레코드 부존재.

**신규**: C1·벤치마크·R2 feature가 사용하는 **데이터 자산**은 L1(어디서 어떻게 보여줄지)과 별개로 **Data Asset Policy(어디서 온 데이터를 어디로 보낼 수 있는지)**를 통과해야 한다 (§4.9).

---

## 3. NULL / N/A / 0 삼분

| 상태 | 의미 | 완결성 지표 | KPI 분모 |
|---|---|---|---|
| `NULL` | 있어야 하는 값이 미입력 | 결측 집계 | 케이스별 정의 |
| `N/A` | 해당 국가/유형에서 미사용 필드 | **집계 제외** | **분모 제외** |
| `0` | 실측값 0 | 정상 | 정상 |

구현: 적용성 매트릭스 분리(B안) 권고 — `country_field_applicability(country, entity, field, applicable)` 참조 테이블 (D-01).
- AC-3.1: N/A 필드는 completeness 분모 미포함.
- AC-3.2: N/A 필드 값 쓰기 시도 422 거부.
- AC-3.3: APPLICABLE→NOT_APPLICABLE 전환 시 기존 데이터 보존, 신규 입력만 차단.

---

## 4. 국가별 KPI 정책 (L1)

### 4.1 개편 사유

단일 `role`은 A-rule·내부 계산·외부 노출을 분리 표현할 수 없다. 6축 정책 벡터로 분리한다:
- 화면에는 숨기되 내부 모델 feature로는 사용하는 KPI
- 농장 UI에는 숨기되 기업 API에는 허용하는 KPI
- **계산은 하되 외부 노출은 금지하는 KPI ← A-rule의 본질**
- 벤치마크 비교는 금지하되 자체 룰 계산은 허용하는 KPI

### 4.2 스키마 — 상속 버그 수정 (v0.3.1 핵심 패치)

v0.3 결함: 정책 6축 전부 NOT NULL → 부분 override 불성립. 수정:

**원본 테이블 — override 축은 전부 nullable**

```sql
CREATE TABLE country_kpi_policy (
    id                    BIGSERIAL PRIMARY KEY,
    scope_level           VARCHAR(16) NOT NULL,  -- GLOBAL|COUNTRY|FARM_TYPE|TENANT
    country_code          VARCHAR(2),
    farm_type             VARCHAR(24),
    production_system     VARCHAR(24),
    herd_size_band        VARCHAR(24),
    tenant_id             BIGINT,
    kpi_code              VARCHAR(64) NOT NULL,
    -- 정책 벡터: NULL = 상위 상속
    compute_enabled       BOOLEAN,
    display_role          VARCHAR(16),           -- PRIMARY|SECONDARY|HIDDEN
    rule_enabled          BOOLEAN,
    benchmark_exposure    VARCHAR(16),           -- FULL|CONTEXT_ONLY|NONE
    prediction_feature    BOOLEAN,
    api_export_policy     VARCHAR(24),           -- PUBLIC|TENANT_ONLY|INTERNAL_ONLY|NONE
    decision_status       VARCHAR(16) NOT NULL,  -- PROPOSED|REVIEWED|APPROVED|REJECTED
    decided_by            VARCHAR(64),
    effective_from        DATE NOT NULL,
    effective_to          DATE,
    note                  TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_scope_keys CHECK (
        (scope_level = 'GLOBAL'    AND country_code IS NULL AND farm_type IS NULL AND tenant_id IS NULL) OR
        (scope_level = 'COUNTRY'   AND country_code IS NOT NULL AND farm_type IS NULL AND tenant_id IS NULL) OR
        (scope_level = 'FARM_TYPE' AND country_code IS NOT NULL AND farm_type IS NOT NULL AND tenant_id IS NULL) OR
        (scope_level = 'TENANT'    AND tenant_id IS NOT NULL)
    ),
    CONSTRAINT chk_global_complete CHECK (
        scope_level != 'GLOBAL' OR (
            compute_enabled IS NOT NULL AND display_role IS NOT NULL AND
            rule_enabled IS NOT NULL AND benchmark_exposure IS NOT NULL AND
            prediction_feature IS NOT NULL AND api_export_policy IS NOT NULL
        )
    ),
    CONSTRAINT chk_approved_decided CHECK (
        decision_status != 'APPROVED' OR decided_by IS NOT NULL
    )
);
```

**해석 결과 — resolved policy (리졸버가 읽는 유일한 소스)**

```
GLOBAL → COUNTRY → FARM_TYPE → TENANT 순으로 NULL 아닌 축만 override
→ resolved_country_kpi_policy (materialized view 또는 버전 태그 캐시)
```

- **리졸버·프론트·API는 원본 테이블 직접 조회 금지. resolved만 읽는다.**
- 재계산 실패 시 이전 버전 유지 + 알람 (신규 정책 미적용 > 잘못된 정책 적용 — fail-closed).
- `decision_status != 'APPROVED'` 행은 resolved 계산에서 제외.

### 4.3 상속 체인

`GLOBAL → COUNTRY → FARM_TYPE(+production_system, herd_size_band 와일드카드) → TENANT`. 하위 우선.

### 4.4 KR 데이터 표현 — §4.9로 이관

v0.3의 KR 정책 벡터 서술은 제품 정책과 데이터 원산지를 혼동한 것. A-rule은 "데이터가 어디서 왔냐"의 규칙 → §4.9 Data Asset Policy 담당. country_kpi_policy에 KR 특수 행 두지 않음.

### 4.5 KPI 카탈로그 연동

카드 없는 KPI는 정책 등록 불가. 카드 규격(yaml): kpi_code / name / formula(문장) / denominator(+주석: PSY 분모=상시모돈, mated female 기준과 상이·외부 수치 대입 금지) / required_inputs / warmup / external_benchmark / outlier_policy / cohort_dimensions[farm_type, production_system, herd_size_band, climate_zone].

### 4.6 매트릭스 (decision_status 명시)

| KPI | US | BR | 기타 | 근거 |
|---|---|---|---|---|
| MSY | display=PRIMARY **(PROPOSED)** | 동일 **(PROPOSED)** | TBD | 회의 방향 2026-07-21. 국가별 자료 미팅에서 확정 |
| PSY | display=SECONDARY **(PROPOSED)** | 동일 **(PROPOSED)** | TBD | 동상 |
| 사산율 | EXCLUDED (APPROVED — 기존 SSOT) | 동일 | 동일 | PigOS 공식=(사산+미라)÷총산, 외부 비교 무효 |
| 이유두수·FCR·ADG·분만율·생존율 계열·경영 KPI 등 | TBD | TBD | TBD | v0.4 실사 대상 |
| 이유~출하 통합생존율·도체등급·방역준수율 | 미구현 | 미구현 | 미구현 | KPI 갭 실사 확인분 |

seed 생성 규칙: **APPROVED 행만.** PROPOSED는 문서에만 존재.
JP: 지원 여부 미결(B-06). CN: v0.4에서 열 신설 (기존 누락).

### 4.7 Override 방향 규칙 — 전 축, 하위는 강화만 가능

| 축 | 하위 허용 방향 |
|---|---|
| compute_enabled | true → false 만 |
| display_role | PRIMARY → SECONDARY → HIDDEN 방향만 |
| rule_enabled | true → false 만 |
| benchmark_exposure | FULL → CONTEXT_ONLY → NONE 방향만 |
| prediction_feature | true → false 만 |
| api_export_policy | PUBLIC → TENANT_ONLY → INTERNAL_ONLY → NONE 방향만 |

위반 시 **저장 시점 거부.**

### 4.8 예외 정책 (Exception Policy)

특정 테넌트 한정 완화(인테그레이터 파일럿 등)는 일반 override가 아니라 별도 승인:

```sql
CREATE TABLE kpi_policy_exceptions (
    id              BIGSERIAL PRIMARY KEY,
    tenant_id       BIGINT NOT NULL,
    kpi_code        VARCHAR(64) NOT NULL,
    axis            VARCHAR(32) NOT NULL,
    override_value  VARCHAR(24) NOT NULL,
    reason          TEXT NOT NULL,
    approved_by     VARCHAR(64) NOT NULL,      -- Decision Register ID
    expires_at      DATE NOT NULL,             -- 만료 필수. 무기한 예외 불가
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

남용 방지: 만료 필수 / Register 등재 / 분기 전수 리뷰 / 예외 다수 발생 = 정책 개정으로 전환.

### 4.9 데이터 원산지 정책 (Data Asset Policy) — A-rule 실제 집행 지점

| 개념 | 질문 | 담당 |
|---|---|---|
| 제품 사용 국가 | 어느 나라 테넌트인가 | country_kpi_policy — 어디서 어떻게 보여줄지 |
| 데이터 원산지 | 이 벤치마크가 한국 데이터로 만들어졌는가 | **Data Asset Policy** — 어디서 온 데이터를 어디로 |

country policy만으로는 "미국 테넌트 응답이 한국 PigPlan 데이터의 재가공"인 경우를 못 막는다. 자산별 lineage:

```yaml
asset_id / source_country / source_system / source_tenants / consent_scope / anonymization_status
allowed_uses:
  internal_calibration: true      # T1/T2 하네스
  tenant_benchmark: false         # KR산: D-07 승인 전 false 고정
  external_api: false
  commercial_sale: false
  model_training: TBD             # AI 학습 동의 연동
```

집행 지점: C1 코호트 구성 / R2 feature 조립 / 외부 API 응답. 소유 문서: `docs/specs/ANONYMIZATION_RELEASE_GATE_SPEC.md`.
- AC-4.9a: tenant_benchmark=false 자산은 어떤 벤치마크 코호트에도 미포함.
- AC-4.9b: 응답 조립 시 자산 lineage 감사 로그 (내부용).

### 수용 기준 (§4)
AC-4.1 compute=false 무평가·무로그 / AC-4.2 HIDDEN&compute=true 산출·비노출 / AC-4.3 INTERNAL_ONLY는 외부 API 미노출 / AC-4.4 비APPROVED 행 리졸버 미로드 / AC-4.5 완화 override 저장 거부(전 축).

---

## 5. KPI 카탈로그
§4.5 규격. 카탈로그 위치: `docs/kpi/catalog/*.yaml` (1파일 1KPI). CONTEXT 클래스(v0.4 priority_class)는 C1과 동일하게 verdict 금지.

## 6. 경영 KPI 도메인

### 6.1 명명 (중요)
lot 귀속·재고·감가 도입 전까지 **"생산비/생산원가" 금지.** 공식 명칭: **기간 운영비** / **현금 기준 손익**. UI·리포트·마케팅 동일 적용. "생산원가" 승격은 lot 모델 도입 시 별도 결정.

### 6.2 입력 자동화 8채널
분만·이유(기존) / 사료 주문(기존) / 약품·백신(신설) / 출하+정산(부분) / 직원 작업완료(신설 — 기록=무료, 관리=유료 경계는 Entitlement) / 센서(신설 — 경계 OPEN) / 음성(신설) / 명세서·사진 OCR(신설, B-08 해소 전 프로덕션 금지).

### 6.3 스키마
- `source_documents` 엔티티: document_type / object_storage_key / checksum / extraction_status / extracted_payload / extraction_model / confidence / reviewed_by. `cost_entries.source_ref TEXT` → `source_document_id FK`.
- **B-08 (보안·보존)**: 암호화·접근통제·signed URL·malware scan·retention·삭제요청·지역저장·외부 OCR 처리자 기록·민감필드 마스킹 — 해소 전 source_documents 프로덕션 가동 금지 (개발·스테이징은 합성 데이터).
- cost_entries / revenue_entries: v1 = vendor_name·tax_included·unit_price·quantity_uom·fx_rate_snapshot(D-02 후)·entry_status·source_document_id. v2 유보 = 거래처 마스터·invoice 체계·credit note·반복 고정비·다농장 배분·lot 귀속·수정 이력.
- 산출: 기간 운영비 = Σcost / 현금 손익 = 매출−운영비 / 두당·kg당 파생. 분모·기간 정의 = D-03.
- soft-delete 엔트리는 전 집계 제외. KR 노출 = D-04 (feature flag OFF 유지).

## 7. 룰 계층과 티어 게이팅

| 계층 | 성격 | 티어 |
|---|---|---|
| R1 룰 기반 경보 | 결정론적, AI 무개입 | 무료 |
| C1 벤치마크 맥락 | verdict 금지 | 무료 |
| R2 특화 예측 | 예측 대상 명명 필수 ("AI 분석 경보" 총칭 금지) | 유료 |

- 게이팅 = 알림 **생성** 시점. 무료 테넌트 DB에 R2 레코드 존재 = 결함 (AC-7.1). R1은 티어 무관 동일 (AC-7.2). R2 실패 시 R1/C1 무영향 (AC-7.4).
- 트라이얼: 1주 체험 → 해지 시 미결제 → 월 과금. 만료 후 기존 알림 = D-05.
- 결제: reserve→commit·idempotency 등은 **BILLING_ARCHITECTURE_NOTE.md 기설계 — 재설계 금지, 참조.** 추가 요청 발신분: reservation expiry / 동일 예측 중복 차감 방지 / entitlement snapshot / price_config↔audit 연결 / trial usage.
- C1 강화 백로그: 코호트 비교 문장형 알림("동일 규모 대비 하위 N%") — cohort_dimensions 확정 전제, verdict 금지 유지.

## 8. 임계값 소스 전략 (L2)

- InterPIG 평균 → 임계값 직접 사용 금지 (평균=컷라인이면 절반이 경고). 용도 = **국가 간 상대 오프셋** + C1 맥락.
- 절차: 기준국 T2 캘리브레이션 → 오프셋 이동 → 실측 보정. rule_configs에 source(CALIBRATED|OFFSET|OPERATIONAL_DEFAULT)·base_country·as_of 기록.
- 가용성: US·BR 분모 일치 확인(기준국 후보 US) / EU·GB BLOCKED(B-01, D-3 선행) / CA·VN·TH MISSING. SEA는 인테그레이터 실데이터 확보 전 operational_default도 근거 없이 생성 금지 (D-06).
- T2 게이트: G1 기준국 선정 → G2 실측 **분포** 확보 (평균만 있으면 FAIL) → G3 백분위 임계 후보 → G4 Golden Suite + 알림량 시뮬레이션 → G5 승인·반영 → G6 타국 오프셋.
- **라이선스(B-02)**: 내부 분석·파생 오프셋 산출의 허용 여부 역시 검토 대상. 법무 확인 전 외부 노출·상업 파생물·제품 반영 전부 금지, 내부 사용도 검토 결과에 따라 소급 중단 가능 전제.

## 9. 표준화 레이어

- `code_mappings`: domain(DISEASE|MEDICINE|VACCINE|FEED_PRODUCT) / source_system / source_code / canonical_code / confidence / mapped_by(HUMAN|RULE|MODEL) / **mapping_status(PROVISIONAL|REVIEWED|REJECTED)**.
- 사용 등급: 분석·미리보기·완결성 = PROVISIONAL 이상(미검토 비율 표기) / **R1 verdict = REVIEWED만, PROVISIONAL 진입 시 판정 보류(fail-closed)+검토 큐** / R2 feature = 모델 카드 정책 / 외부 판매 = REVIEWED 또는 Release Gate 품질등급 이상.
- 이상치: KPI 카드별 outlier_policy (전역 일괄 금지). 근거 문서 없으면 raw + flag. VALID_EXTREME(축소농장) = DEFERRED(B-03).
- 단위: **저장 SI 고정**, 표시 계층에서만 변환. 왕복 불변 (AC-9.1).
- 코호트 차원 표준(§9.5): herd_size_band(구간 TBD 실사) / farm_type(피그플랜 분류 대조) / production_system(D-3 연동) / climate_zone(기존 체계 검토, 자체 발명 금지).

## 10. 데이터 이관과 A-rule
KR 데이터의 해외 비교 노출 = D-07 (대표 보고·결정). 정책 벡터·Asset Policy가 있어도 승인 없이 tenant_benchmark를 열지 않는다. 이관 P1 선행 = Oracle 타임스탬프 감사(B-04).

## 11. 온보딩 최소 입력 세트
resolved policy의 display_role=PRIMARY KPI들의 required_inputs 합집합 = 최소 세트. 워밍업 포함 "N일 후 첫 지표" 안내. AC-11.1: 최소 세트만으로 PRIMARY 1개 이상 산출. (기존 docs/specs/2026-07-10_signup-onboarding-spec.md와 정합 확인 필요)

## 12. 테스트 계획

기존 프레임 유지: T1/T2 분리 · Golden Suite+Rolling Replay · available_at 누출 방지 · internal_reference fail-closed · EWMA/CUSUM 워밍업 제외. 골든 기대값은 스펙 산식으로만 도출(역기입 금지).

| ID | 검증 |
|---|---|
| T-A1' | 정책 벡터: compute=false 무평가 / HIDDEN&compute 분리 |
| T-A3 | PROPOSED 행 리졸버 미로드 |
| T-A4~A7 | 전 축 완화 override 저장 거부 |
| T-A5 | 부분 override 상속 |
| T-A6 | scope CHECK (GLOBAL 완전성 포함) |
| T-A8 | 예외 만료 미반영 |
| T-A9 | resolved 전용 접근 (원본 직접 조회 부재) |
| T-L1 | tenant_benchmark=false 자산 코호트 0건 |
| T-R1~R4 | 런타임 게이트: 미등록 국가 가입 차단 / Release 미통과 결제 차단 / 동의 없는 리드 0건 / 미승인 기능 판매 차단 |
| T-V1 | envelope 필수 필드 거부 |
| T-B/C/D/E/F/H | v0.2~0.3 정의 유지 (운영비 명칭 반영, source_documents FK 무결성 추가) |

## 13. 결정 등록부·블로커

D-01 N/A 방식(B안 권고, CTO) / D-02 통화(원본보존, CTO) / D-03 기간귀속(대표) / D-04 경영 KR 노출(대표) / D-05 트라이얼 만료 알림(CTO) / D-06 SEA default(CTO) / D-07 KR 해외 노출(대표) / D-08 두수 무제한(대표) / D-09 경영 P0(대표) / D-10 R1/R2 경계(대표, Entitlement 일괄) / D-3 GB indoor·outdoor(CTO, 기존).

B-01 EU/GB 차단 / B-02 AHDB 라이선스 / B-03 VALID_EXTREME / B-04 Oracle 감사 / B-05(=D-07) / B-06 일본 / B-07 보고서·인사이트 중복 / B-08 문서 보안·보존.

## 14. 실행 로드맵

**원칙: Phase 0는 코딩 중지 게이트가 아니라 오픈 게이트다.**

### 14.1 런타임 오픈 게이트 (코드가 강제)
```
country_launch_registry.can_signup(country_code)
entitlement_registry.can_sell(country_code, feature_code)
release_gate.is_approved(data_product_id)
consent_service.has_purpose(tenant_id, 'TRANSACTION_MATCHING')
```
- 미통과 시 명시적 예외, silent fallback 금지.
- **registry 행도 결정이다**: decided_by·approved_at 필수 — 근거 없는 오픈 행은 스키마상 불가.
- CI 상시: T-R1~R4.

### 14.2 Phase
P0(오픈 게이트 문서 — INDEX 참조) → P1(정책 벡터 §4 · 카탈로그 · 코호트 §9.5 · **Envelope §15 고정** · D-01~03) → P2(경영 KPI · source_documents · R1 · C1 강화 · 온보딩 최소입력) → P3(R2 카탈로그(B-07 후) · 트라이얼 · BILLING 추가) → P4(B-01·02 해소 → 벤치마크 · T2 G1~G6 · D-07 · 이관 P1).

## 15. Canonical Event Envelope (Phase 1 고정)

완전한 Canonical Model은 유예(3번째 국가 시 착수)하되 최소 이벤트 계약은 지금 고정:

```yaml
event_id / tenant_id / farm_id / country_code / farm_type / event_type
occurred_at / available_at        # 분리 필수 — 미래데이터 누출 방지 원칙의 승격
source_system                     # MANUAL|PIGPLAN_IMPORT|OCR|VOICE|SENSOR|API
source_document_id / source_record_id
canonical_code / raw_value / canonical_value / canonical_unit(SI)
currency / mapping_status / quality_status
consent_scope / data_origin_country   # §4.9 lineage의 이벤트 레벨 태그
created_at
```
envelope 미준수 이벤트 수용 거부 (T-V1).

## 변경 이력
| v0.1~0.3 | 2026-07-21 | 골격→상세화→GPT 1차 반영 |
| v0.3.1 | 2026-07-21 | GPT 2차 반영: nullable 상속+resolved, 전축 완화 금지, 예외 정책, 원산지 분리, 런타임 게이트, Envelope, B-08 |
