# OPEN_QUESTIONS v1.2 — 미결 항목 통합 집계 (2026-07-21)

> 성격: 전 산출물의 미결 항목을 해소 경로별로 집계. 상세 질의문은 LAWYER_BRIEF.md (30건). 상태값은 아래 enum 고정.
> **상태 enum**: PROPOSED / BUSINESS_APPROVED / COUNSEL_PENDING / TECHNICAL_VERIFICATION_PENDING / IMPLEMENTATION_PENDING / BLOCKED / REOPENED / CLOSED / NOT_APPLICABLE. (한 항목이 여러 트랙 대기면 OVERALL은 가장 강한 차단값.)

## A. 의사결정 항목 (DECISION_REGISTER)

| ID | 항목 | BUSINESS | COUNSEL | OVERALL | 반영 위치 |
|---|---|---|---|---|---|
| D-01 | 목적② 국가별 법적 근거 분기 | APPROVED | PENDING | BLOCKED | MASTER 제10조③, NOTICE 제3조, CONSENT_SPEC §2, ADDENDA 각 제4조 |
| D-02 | ③④⑤ 옵트인·기본 OFF·개별 토글 | APPROVED | PENDING | BLOCKED | MASTER 제10조②, CONSENT_SPEC §3.1 |
| D-03 | 20년 삭제·익명 산출물 존속 구조 | APPROVED | PENDING | BLOCKED | MASTER 제16조, **NOTICE 제9조** |
| D-04 | 소급회수 불가 적용 범위 한정 | APPROVED | PENDING | BLOCKED | MASTER 제10조⑤, CONSENT_SPEC §4 |
| D-05 | 릴리스 게이트 수치 (k=10/20·지배율 — 후보값) | 미결 | PENDING | OPEN | ANONYM_STANDARD §2.4·§8, ADDENDUM_EU·GB COUNSEL NOTES |
| D-06 | KR 코호트 5 이원 vs 전사 상향 | 미결 | PENDING | OPEN | ANONYM_STANDARD §7 |
| D-07 | 중국 진입 구조 | 미결 | PENDING | OPEN (HOLD) | internal/INTERNAL_LAUNCH_GATE_CN |
| D-08 | 베트남 출시 게이트 해제 | 미결 | PENDING | OPEN (HOLD) | internal/INTERNAL_LAUNCH_GATE_VN |
| D-09 | 태국 출시 게이트 해제 | 미결 | PENDING | OPEN (HOLD) | internal/INTERNAL_LAUNCH_GATE_TH |
| D-10 | 콜드 이메일 게이팅·KR 중단 | PROPOSED | — | PROPOSED | CONSENT_SPEC §7 |
| D-12 | 데이터 수익 배분 모델 | 미결(사업) | — | OPEN | 마스터 제6조 코멘트, DATA_REVENUE_SHARE_POLICY(미작성) |
| D-13 | controller/processor 역할 | 미결 | PENDING | OPEN | NOTICE 제7조, PIGOS_B2B_DPA_DRAFT |
| D-14 | 조직 대리 동의 범위 | PROPOSED | PENDING | PROPOSED | MASTER 제4조⑥ |
| D-15 | 유료/무료 경계 | 미결(사업) | — | OPEN | MASTER 제2·5·6조 |

**집계 (총 14건)**: BUSINESS_APPROVED+COUNSEL_PENDING 4 (D-01~04) · OPEN 8 (D-05·06·07·08·09·12·13·15) · PROPOSED 2 (D-10·14). **미종결 합계 10건** (조건부 승인 4건은 COUNSEL 회신까지 열림). D-11은 D-01로 흡수(종결).

> † D-01~D-04: 2026-07-21 대표 조건부 승인(BUSINESS_APPROVED). COUNSEL 회신 후 CLOSED, 반대 시 REOPENED. 검토자는 이 4건을 신규 P0로 재상정하지 말고 이견 시 REOPEN 후보로만 표시.

## B. 미결 사업조건 (임의 확정 금지 — [OPEN] placeholder) — 8건

| 항목 | 위치 |
|---|---|
| 손해배상 상한 | MASTER 제15조④ |
| 크레딧 유효기간·가격·차감 기준 | MASTER 제6조②③ (가격표 정책 미작성) |
| 환불 세부 기준 | MASTER 제6조④ (유료 서비스 정책 미작성) |
| SLA 수치 (구 95.0% 약관서 제거) | MASTER 제15조④ (SLA 정책 미작성) |
| 시행일·경과조치 (기존 피그플랜 회원 관계) | MASTER 부칙 |
| 외부 AI 수탁자 목록 | **NOTICE 제8조 표** |
| 개인정보보호책임자·연락처 현행화 (F2) | NOTICE 제1조 |
| EU/UK Art.27 대리인, TH §37(5) 대리인, BR DPO 지정 주체 | ADDENDA 각 제1~2조 |

## C. 변호사 확인 ([COUNSEL] — LAWYER_BRIEF 30건)
전체 목록·우선순위는 LAWYER_BRIEF.md. HIGH: 익명화·판매모델 성립요건, 목적② 분기 적법성, F5(KR 게시본 vs 운영 불일치), 소급회수·존속 방어, 국외이전(VN TIA·TH SCC·BR SCC), CAN-SPAM·NE LB525, CN 진입구조, 재동의 경계선, 조직 대리동의 유효성(D-14), controller/processor 확정(D-13).

## D. 운영·기술 검증 (TECHNICAL_VERIFICATION / OPERATIONS) — 15건
| ID | 항목 | 트랙 |
|---|---|---|
| V1 | 동의 UI·로그 실사 (F5 연결) | OPERATIONS |
| V2 | 앱 내 약관 버전 | OPERATIONS |
| V3 | 구약관(2026-05-30 이전) 확보 | OPERATIONS |
| V4 | PigSignal 기제공 이력·수신처 계약 | OPERATIONS |
| V5 | 콜드 이메일 발송 현황 | OPERATIONS |
| V6 | 실제 수탁자·하위처리자 전체 목록 | TECHNICAL |
| V7 | 서버·DB·백업·로그·CDN 처리 국가 | TECHNICAL |
| V8 | GA/CMP 사전동의 차단 구현 | TECHNICAL |
| V9 | 외부 AI no-training·zero-retention 계약 상태 | TECHNICAL/LEGAL |
| V10 | 데이터 유형별 실제 보유기간·백업 삭제주기 | TECHNICAL |
| V11 | 조직·농장·사용자 권한 및 대리동의 구현 | TECHNICAL |
| V12 | consent ledger·withdrawal·downstream exclusion 구현 | TECHNICAL |
| V13 | 익명화 배치·release gate 구현 및 릴리스 이력 | TECHNICAL |
| V14 | 데이터 export·탈퇴·삭제 프로세스 | TECHNICAL/OPERATIONS |
| V15 | 결제·크레딧·환불 실제 처리 흐름 | TECHNICAL/OPERATIONS |

## E. 증거 등급 보강 (스냅샷 TODO) — 3건
T1 렌더링 PDF·HTML 아카이브 / T2 앱 내 게시본 / T3 구버전 약관.

## F. 게시 전 필수 문서 — 트리거별 (모두가 글로벌 게시를 막는 것은 아님)
| 문서 | 트리거 | 적용 국가/기능 | 글로벌 게시 차단 | 상태 |
|---|---|---|---|---|
| BR ANPD SCC 전문·기입본 | 브라질 출시 | BR | 아니오 (BR만) | 미확보 |
| TH 국외이전 계약 | 태국 출시 | TH | 아니오 | 미확보 |
| EU·UK 대리인 지정서 | EU·GB 출시 | EU·GB | 아니오 | 미지정 |
| VN TIA·DPIA | 베트남 출시 | VN | 아니오 | 미확보 |
| US 주별 State Schedule 전문 | 미국 출시 | US(각 주) | 아니오 | 미완 |
| 쿠키 정책·CMP | 비필수 쿠키 사용 국가 | EU·GB 등 | 해당 국가 차단 | 미구현 |
| 유료·환불 정책 | 유료 기능 출시 | 유료 기능 | 유료 기능 차단 | 미작성 |
| SLA | SLA 판매·약속 시 | 유료/기업 | 해당 시 차단 | 미작성 |
| 익명화·릴리스 표준 확정본 | PigSignal·목적② 가동 전 | 전역(목적②·PigSignal) | **예 (판매 차단)** | 초안(수치 미확정 D-05) |
| DPA·하위처리자 목록 | 기업·조직 고객 계약 전 | B2B 고객 | B2B 계약 차단 | 초안(D-13) |
| LIA / DPIA | 목적②·기업고객 처리 전 | 해당 처리 | 해당 처리 차단 | 미작성 |
| DATA_REVENUE_SHARE_POLICY | **수익배분 모델 도입 시에만** | 도입 시 | 아니오 | N/A (미도입) |

## G. 실행 통제 게이트 (문서가 아니라 즉시 조치)
| 게이트 | 조건 | 상태 |
|---|---|---|
| **CURRENT NOTICE ↔ ACTUAL PROCESSING ALIGNMENT** | KR 게시본("별도 동의") vs 실제 운영(옵트아웃) 불일치(F5). 해소 전 최소 1개 실행: ①목적② 활용 임시중단 ②신규 데이터 PigSignal 집계 제외 ③게시문구·동의 UI를 실제 운영에 임시 정렬 ④실제 별도동의 수집·로그 보존 | **BLOCKED until F5 resolved** |

## 집계 (중복 가능 — 단순 합산 금지)
- 의사결정: 14건 (BUSINESS_APPROVED+COUNSEL_PENDING 4 / OPEN 8 / PROPOSED 2 / 미종결 10)
- 사업조건 placeholder: 8건 · 변호사 질의: 30건 · 운영·기술 검증: 15건 · 증거 보강: 3건 · 실행 게이트: 1건(BLOCKED)
