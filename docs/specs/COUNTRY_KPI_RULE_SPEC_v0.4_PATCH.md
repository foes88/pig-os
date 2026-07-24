# COUNTRY_KPI_RULE_SPEC v0.4 — 정책 벡터 구조 패치 (v0.3.1 위에 적용)

> 성격: v0.3.1 §4(국가별 KPI 정책)를 확장. **구조(structure)는 채택 확정(검증 불요)** — 근거: 2026-07-21 회의 방향 + GPT 교차리뷰 초안(`docs/kpi/gpt_country_draft_UNVERIFIED.md` "구조 제안 채택 확정분").
> **값(어느 국가에 어느 KPI·수치)은 여전히 위조0** — evidence 확보 + APPROVED 전까지 seed 금지.
> 검증된 정의는 `docs/specs/COUNTRY_KPI_DEFINITION_MATRIX.md`(deep-research V1~V7)를 SSOT로 참조.

---

## 0. v0.3.1 대비 델타 (무엇이 바뀌나)

| # | 변경 | v0.3.1 | v0.4 |
|---|---|---|---|
| D1 | **priority_class 신설** | display_role = PRIMARY\|SECONDARY\|HIDDEN (3) | **6분류** NORTH_STAR\|DRIVER\|GUARDRAIL\|FINANCIAL\|QUALITY\|CONTEXT. display_role은 파생(호환) |
| D2 | **evidence_status 축 분리** | decision_status만(승인 여부) | evidence_status(출처 강도) **별도 축** — 승인과 무관하게 "얼마나 검증됐나" |
| D3 | **production_stage 명시** | production_system(자유) | BREEDING\|NURSERY\|GROW_FINISH\|FARROW_TO_FINISH 표준값 |
| D4 | **EU 단일 프로필 폐기** | "EU" 묶음 | 회원국 개별(DK/FR/DE/ES/NL/IE) + GB 별도. 지역 프리셋은 상속으로만 |
| D5 | **country 확장** | US/BR/KR/CN/VN/TH | + JP·GB·DK·FR·IE(후보, UNVERIFIED_DRAFT) |
| D6 | **승인 게이트 G-C1~C8** | 암묵 | KPI 국가 프로필 승격 8단계 게이트 명문화 |

나머지(상속체인·리졸버·override방향·A-rule·위조0)는 v0.3.1 유지.

---

## 1. priority_class (6분류) — KPI가 화면/알림에서 하는 역할

| class | 의미 | UI 배치 | verdict | 예(미확정) |
|---|---|---|---|---|
| **NORTH_STAR** | 시스템 대표 1지표 | Hero 카드 최상단 1개 | 허용 | F2F=MSY, 번식전업=PSY (국가별 다름) |
| **DRIVER** | 대표를 움직이는 핵심 동인 | 주요 KPI 카드 | 허용 | 분만율·실산·이유전폐사·FCR·ADG |
| **GUARDRAIL** | 넘으면 경보(방어선) | 알림/룰 엔진 | R1 결정론만 | 모돈폐사·질병발생·데이터신선도·약품사용 |
| **FINANCIAL** | 재무 성과 | 경영 KPI 섹션 | 허용(현금기준) | 기간운영비·현금손익·두당마진 |
| **QUALITY** | 산출물 품질/규격 | 리포트 | 허용 | 도체등급·백파트·균일도·이유체중 |
| **CONTEXT** | 맥락 참고(판단 금지) | 보조 표기만 | **금지(C1과 동일)** | 벤치마크 맥락·코호트 위치 |

- **display_role 파생 매핑**(호환): NORTH_STAR·DRIVER→PRIMARY / FINANCIAL·QUALITY→SECONDARY / GUARDRAIL→(룰만, 카드 HIDDEN) / CONTEXT→SECONDARY(verdict금지).
- NORTH_STAR는 (country × farm_type × production_stage) 조합당 **정확히 1개** (CHECK).
- GUARDRAIL·CONTEXT는 verdict 금지(기존 C1 규율 승계).

## 2. evidence_status (출처 강도) — decision_status와 직교

> **두 축을 분리하는 이유**: "승인됐다(쓴다)"와 "검증됐다(출처있다)"는 다르다. 미검증인데 임시 승인(보수 운영)도, 검증됐는데 미승인(대기)도 가능해야 함.

| evidence_status | 뜻 | 근거 예 |
|---|---|---|
| VERIFIED | 1차 권위 출처 원문 대조 | PorkGateway·NIAS·EUR-Lex·Koketsu(deep-research V1~V7) |
| OFFICIAL_GUIDANCE | 공식 기관 가이드(원문) | ICO·ANPD·EDPB 등 |
| DRAFT_GUIDANCE | 초안·의견수렴 단계 | EDPB 02/2026 초안 |
| REVIEWED_DIRECTION | 방향 검토됨, 출처 부분 | 회의 확정 방향 |
| UNVERIFIED_DRAFT | 미검증(모델 생성 등) | GPT 국가초안·미대조 인용 |
| INSUFFICIENT | 자료 낡음/표본부족 | TH 시험농장 자료 |

- **출처 우선순위 5단계**(GPT초안 채택): ① 정부/법령 ② 국가 기록시스템 공식정의(PigCHAMP/Agriness/PigPlan) ③ 산업협회 벤치마크 ④ 피어리뷰 논문 ⑤ 그 외. 상위 없으면 하위, 전무면 빈칸.
- **seed 게이트**: `decision_status='APPROVED' AND evidence_status IN ('VERIFIED','OFFICIAL_GUIDANCE')` 만 benchmark 수치 seed 허용. 그 외는 policy 행만(수치 없이) 또는 문서 격리.

## 3. production_stage (표준 차원)

`BREEDING | NURSERY | GROW_FINISH | FARROW_TO_FINISH`. farm_type과 조합해 KPI 프로필 결정(예: US·F2F NORTH_STAR=MSY / US·BREEDING NORTH_STAR=PW/MF/Y). GPT초안의 국가×stage 구조를 표준화.

## 4. country_kpi_policy 스키마 (v0.3.1 §4.2 + v0.4 컬럼)

v0.3.1 §4.2 테이블에 **3컬럼 추가**(전부 nullable override 축):
```sql
ALTER TABLE country_kpi_policy
  ADD COLUMN priority_class   VARCHAR(16),   -- NORTH_STAR|DRIVER|GUARDRAIL|FINANCIAL|QUALITY|CONTEXT
  ADD COLUMN production_stage  VARCHAR(16),  -- BREEDING|NURSERY|GROW_FINISH|FARROW_TO_FINISH
  ADD COLUMN evidence_status   VARCHAR(24);  -- VERIFIED|OFFICIAL_GUIDANCE|DRAFT_GUIDANCE|REVIEWED_DIRECTION|UNVERIFIED_DRAFT|INSUFFICIENT
-- CHECK: (country,farm_type,production_stage)당 NORTH_STAR 정확히 1 (resolved 기준)
-- CHECK: decision_status='APPROVED' → evidence_status NOT IN ('UNVERIFIED_DRAFT','INSUFFICIENT') (미검증 승인 금지, 단 임시보수는 note로 예외기록)
```
> ⚠️ `country_kpi_policy` 테이블 자체가 **아직 미구현**(v3.1 거버넌스는 kpi_definitions·source_observations·benchmarks 3테이블만 존재). v0.4-P1에서 이 테이블 신설(마이그레이션) 필요. 상속·resolved view·리졸버는 v0.3.1 §4.2~4.3 그대로.

## 5. 승인 게이트 G-C1~C8 (국가 KPI 프로필 승격)

UNVERIFIED_DRAFT → APPROVED 승격은 8게이트 통과 필수(하나라도 미충족 시 승격 불가):
1. **G-C1 카드 존재**: kpi_definitions에 formula·denominator·denominator_type 정의됨.
2. **G-C2 정의 검증**: evidence_status ≥ OFFICIAL_GUIDANCE (1차 출처 대조).
3. **G-C3 분모 명시**: denominator_type 확정(외부 수치 대입 무효 여부 태그).
4. **G-C4 stage·farm_type 귀속**: production_stage·farm_type 확정.
5. **G-C5 priority_class 배정**: NORTH_STAR 유일성 검증 통과.
6. **G-C6 임계 출처**(수치 seed 시): source_observations에 source_year·denominator 있는 관측 ≥1.
7. **G-C7 비교 유효성**: 정의 상이 지표(사산율·모돈도폐사율 등)는 external_benchmark=INVALID 태그.
8. **G-C8 결정 기록**: decided_by·approved_at + note. 근거 없는 APPROVED 스키마상 불가.

## 6. 현재 상태 반영 (위조0)

- **APPROVED(GLOBAL, 즉시 seed 가능)** — 코드 구현된 SSOT KPI: PSY·NPD·모돈회전율·분만율·이유전폐사·WSI·RTS·실산·이유두수·FCR·ADG·MSY. 사산율=EXCLUDED(외부비교 무효, 기존 SSOT). 정의는 deep-research V1~V7·MATRIX 참조.
- **VERIFIED 정의(국가차, 값은 미승인)**: PSY 분모(US=교배모돈)·NPD 여집합·회전율 2정의·모돈도폐사≠removal·EU 이유일령28 (V1~V7). → 정의는 evidence=VERIFIED이나 **국가별 policy 행은 G-C 게이트 통과 후**.
- **UNVERIFIED_DRAFT(문서격리, seed 금지)**: GPT초안 국가별 KPI 후보 전체(US/BR/GB/DK/FR/IE/CN/VN/TH/JP). priority_class 후보만 문서에 기록, policy 테이블 미반영.
- **미확보(빈칸)**: PigCHAMP/PigPlan 1차문서·사산율 미라포함·MSY 정의·China WEPIG·각국 법정 이유일령(EU 외).

## 7. v0.4 구현 단계 (P1)

1. **country_kpi_policy 테이블 신설**(마이그레이션) — §4 스키마(v0.3.1 §4.2 + v0.4 3컬럼).
2. **GLOBAL scope seed** — 위 APPROVED SSOT KPI 12종 + 사산율 EXCLUDED. priority_class 초기 배정(NORTH_STAR=MSY[F2F]/PSY[BREEDING], DRIVER=분만율·실산·이유전폐사·FCR·ADG, GUARDRAIL=모돈폐사, CONTEXT=벤치마크맥락).
3. **resolved view + 리졸버**(v0.3.1 §4.2~4.3) — APPROVED만, evidence 게이트 적용.
4. 프론트/룰엔진은 resolved만 조회(원본 금지).
5. 국가별 override 행은 **G-C 게이트 통과분만** 순차 추가(Phase B evidence 확보 후).

## 8. 수용 기준
- country_kpi_policy 미승인·UNVERIFIED_DRAFT 행은 resolved에서 제외(§4.2 fail-closed 승계).
- NORTH_STAR 유일성 CHECK 위반 시 마이그레이션/seed 실패.
- GPT초안 값이 코드·seed에 유입 0(문서 격리 유지). 테스트로 강제.
