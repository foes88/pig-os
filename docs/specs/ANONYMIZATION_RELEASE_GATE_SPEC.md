# ANONYMIZATION_RELEASE_GATE_SPEC v0.1 (SKELETON)
## 익명화·데이터 자산 정책·판매 게이트

> **상태**: SKELETON. **역할 2개**: ① Data Asset Policy(원산지 lineage) 소유 = **A-rule 런타임 집행 SSOT** ② PigSignal 판매 오픈 게이트 (release_gate.is_approved()).
> **근거**: 2026-07-21 회의 §3.4·§5 · 법무 분석(익명≠가명) · COUNTRY_KPI_RULE_SPEC v0.3.1 §4.9

---

## 1. Data Asset Policy (자산 lineage)
```yaml
asset_id / source_country / source_system(PIGPLAN|PIGOS|IMPORT) / source_tenants / consent_scope
anonymization_status: RAW | PSEUDONYMIZED | ANONYMIZED | AGGREGATED
allowed_uses:
  internal_calibration:   # T1/T2 하네스
  tenant_benchmark:       # KR산 = false (D-07 승인 전 고정)
  external_api:
  commercial_sale:
  model_training:         # AI_MODEL_TRAINING 동의 연동
```
집행 지점: C1 코호트 구성 / R2 feature 조립 / 외부 API 응답 / PigSignal 상품 빌드. lineage 감사 로그 필수.

## 2. 익명화 판정 (법무 분석 확정 방향)
- **가명 ≠ 익명**: Farm-001식 치환 = 가명정보(대응표 재식별 가능) → 판매 불가
- 가명정보 무동의 활용 = 통계·과학적연구·공익기록 한정. "유상 판매"가 자동으로 연구가 되지 않음
- 판매 가능 기본형 = 집계정보

## 3. Release Gate 체크리스트
| 항목 | 기준 |
|---|---|
| 최소 코호트 | 집계군당 최소 농장 수 — 10 vs 20 **TBD** |
| dominance | 특정 농장 과다 비중 시 미공개 — 임계 TBD |
| 희귀 조합 | 상위 집단 병합 |
| 지역 | 정확 주소 금지 → 시·도/권역 |
| 규모 | 정확 두수 금지 → 구간 |
| 시간 | 일 단위 금지 → 주·월·분기 |
| 극단값 | 제거 또는 상·하한 |
| 재식별 위험 | 구매자 결합 시나리오 검토 — 절차 TBD |
| 계약 | 구매자 재식별·재판매·타깃영업 금지 |
| 법무 | 4건 완료 전 판매 개시 불가 |
| audit | 승인자·일시·기준 버전 기록 |

기준례: ❌ "7/13 용인시 ○○면 모돈 1,380두 농장 PRRS" / ✅ "7월 경기 남부 모돈 500두 이상 농장군 호흡기 이상징후 전월 대비 18%↑". 삭제 후에도 특정 가능("○○면 유일 1,200두")하면 익명 아님. **농장 좌표(날씨 기능용)도 외부 노출 불가 자산.**

## 4. 자동 생성 연동
게이트 기준을 기계 판독 config로 제공, AI 생성 상품도 동일 게이트 통과 필수 (자동 생성 ≠ 게이트 우회).

## 5. TBD
최소 코호트 수 / dominance 임계 / 재식별 평가 절차 / status별 허용 매트릭스 / KR 자산 목록 초기화

## 변경 이력
| v0.1 | 2026-07-21 | 스켈레톤 |
