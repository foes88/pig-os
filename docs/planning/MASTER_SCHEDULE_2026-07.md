# MASTER_SCHEDULE_2026-07 v0.1
## 무료·데이터공유 실행 통합 일정

> **원칙**: 날짜 일정 + 조건 게이트 이원 관리. 게이트는 날짜가 아니라 조건 — 충족 전 해당 오픈 행위 금지 (런타임 게이트가 코드로 강제).
> **변수**: `[대표미팅]` = 국가 KPI 실사 완료 후 요청 (목표: 이번 주 후반~다음 주 초). 날짜 확정 시 본 문서 갱신.

## 이번 주 (7/21 주)

| 일 | 항목 | 상태 |
|---|---|---|
| 월(오늘) 밤 | 밤샘 런 A(정책벡터)·B(Envelope)·C(v0.4+evidence+결정요청서)·D(법무 리서치) 실행 — 플레이스홀더 채운 후 | ☐ |
| 화 오전 | 런 4개 결과 리뷰: A/B 게이트 확인, C의 v0.4·CEO_DECISION_BRIEF 검토, D의 LAWYER_BRIEF 검토 | ☐ |
| 화 | CTO 결정: D-01(N/A B안)·D-02(통화)·D-05·D-06 → Register 갱신 | ☐ |
| 화 | Entitlement Matrix GPT 공격 리뷰 → 수정 → **대표 결재 상신** | ☐ |
| 화~수 | Claude legal 실행: LAWYER_BRIEF 입력 → 법무 4건+동반질의 검토 → 변호사 의뢰 발송 | ☐ |
| 수~금 | US KPI 실사 (evidence/US.md UNVERIFIED→REVIEWED_DIRECTION, 웹 원문 대조) + 밸류 프로포지션 병합 | ☐ |
| 주중 | `[대표미팅]` 요청 — 안건: ①Entitlement 결재 ②D-07 ③B-06 ④Matrix 예외 (+D-03·D-04) + 국가 KPI 자료 | ☐ |

## 다음 주 (7/28 주)

| 항목 | 조건 |
|---|---|
| VN·TH·CN 실사 → BR | US 실사 방법 확립 후 |
| `[대표미팅]` 실시 → 결정 6건 확보 | CEO_DECISION_BRIEF + 실사 자료 |
| D-02·03 확정 → 경영 KPI 구현 런 (cost/revenue/source_documents) | 미팅 후 |
| Entitlement 승인 → entitlement_registry + 게이팅 구현 런 | 결재 후 |
| Consent Spec 살 붙이기 (변호사 1차 회신 반영) | 의뢰 회신 |

## 조건 게이트 (날짜 아님)

| 오픈 행위 | 조건 |
|---|---|
| 신규 국가 가입 오픈 | Consent 승인 + 해당 국가 약관 + Ledger 가동 |
| 유료 판매 오픈 | Entitlement 결재 (D-08·09·10) |
| PigSignal 상품 판매 | Release Gate 가동 + 법무 4건 |
| 거래연결·리드 | TRANSACTION_MATCHING 옵트인 + 규제 검토 |
| 농장주 콜드 발송 | 런 D §T1-③ + 변호사 확인 (국가별 상이) |
| InterPIG UI 노출 | B-02 라이선스 |
| source_documents 프로덕션 | B-08 보안·보존 정책 |
| EU/GB 벤치마크 로딩 | D-3 결정 + 분모 검증 (B-01) |
| 피그플랜 이관 P1 | B-04 Oracle 타임스탬프 감사 |

## 별도 트랙 (본 일정 비관리, 참조만)
통합 제품소개서·회사소개서(Entitlement 승인 후 무료 문구) / 블로그 2차(Matrix 예외 후) / 농장주 DB 수집(진행 중) / PigSignal AgentExchange 심사(대기) / 신문사 제안(별도 프로젝트).

| v0.1 | 2026-07-21 | 초판. 대표미팅 날짜 변수형 |
