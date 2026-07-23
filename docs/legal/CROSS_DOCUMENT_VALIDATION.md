# CROSS_DOCUMENT_VALIDATION v1.2 (정본, 2026-07-21)

> 현재 정본. 이전 회차(v1.0 초판, v1.1 P0개정후, v1.2 교차참조)의 낡은 수치·PASS는 §변경이력으로 요약하고 본 표만 유효하다. 파일 수는 FILE_MANIFEST.md 기준.
> **PASS의 의미를 층으로 분리**: DOCUMENT(문서에 반영됨) / LEGAL(법적 유효성) / TECHNICAL(구현·운영 실측) / BUSINESS(사업 결정). DOCUMENT PASS가 LEGAL·TECHNICAL PASS를 의미하지 않는다.

## 1. GPT 레드라인 P0 반영 — 층별 판정

| 검사 | DOCUMENT | LEGAL | TECHNICAL | 비고 |
|---|---|---|---|---|
| 피그플랜 정의 잔존 | PASS | — | — | 잔존 2건 의도된 참조(손배 예시·경과조치) |
| 20년 삭제 | PASS | COUNSEL_PENDING (D-03) | — | 존속구조 방어는 변호사 |
| 수익배분 본문 삭제 | PASS | — | — | 코멘트/OPEN만 |
| CN 고객 부속조항 제거 | PASS | — | — | internal/INTERNAL_LAUNCH_GATE_CN |
| EU/GB 분리 | PASS | — | — | 2벌 + 내부 상호 정합 확인 |
| 공개 부속 k수치 제거 | PASS | — | — | 고객 본문 무수치, COUNSEL NOTES만(게시전 제거) |
| 과금 표현 완화 | PASS | — | BUSINESS OPEN (D-15) | 실제 경계는 사업 결정 |
| 조직 관리자 동의 권한 한정 | PASS (제4조⑥) | **OPEN (D-14)** | TECH_VERIF (V11) | 개별 정보주체 동의 대체 가능성 미확정 |
| 서비스개선/AI학습 분리 | PASS (제9조) | — | — | |
| controller/processor + DPA | **DOCUMENT PASS** | **OPEN (D-13) — LOCAL COUNSEL** | **TECH_VERIF (V6·V12)** | 역할 배분·processor↔PigSignal 전환경로 미해소 |
| VN 매매해석 중립화 | PASS | LOCAL COUNSEL (Q4) | — | ⑤ 비활성 운영 유지 |
| lawful basis 문서 일관성 | **CROSS-DOC PASS** | **COUNSEL_PENDING (D-01)** | — | + LIVE NOTICE ALIGNMENT: **FAIL/OPEN (F5)** |
| GA·쿠키 방침 반영 | **COVERAGE PASS** | — | **CMP/사전차단·벤더설정 TECH_VERIF (V8)** | 문구 O, 구현 미검증 |
| 고객/내부 문서 분리 | PASS | — | — | internal/ + VN·TH 게이트 분리(신규) |

**핵심**: controller/processor(D-13)·조직 대리동의(D-14)·GA(V8)·lawful basis(D-01, F5)는 **문서 PASS ≠ 법적/기술 PASS**. 특히 processor로 받은 계약농가·직원 데이터를 PigSignal·AI학습으로 전환하는 경로가 있으면 D-13은 자문이 아니라 **B2B 출시 P0**.

## 2. 교차참조 무결성 — 증거표 (전수)

| 출발 문서·위치 | 참조 문구 | 실제 대상 | 번호 | 의미 | 결과 |
|---|---|---|---|---|---|
| OPEN_Q A/D-03 | NOTICE 제9조 | 보유기간 | ✓ | ✓ | 수정완료(구 제7조) |
| OPEN_Q B/외부AI | NOTICE 제8조 표 | 위탁·국외이전 | ✓ | ✓ | 수정완료(구 제6조) |
| OPEN_Q B/손배·SLA | MASTER 제15조④ | 책임제한·손배 | ✓ | ✓ | 수정완료(구 제20조④) |
| OPEN_Q A/D-01 | MASTER 제10조③ | 목적② 국가분기 | ✓ | ✓ | OK |
| OPEN_Q A/D-02 | MASTER 제10조② | ③④⑤ 옵트인 | ✓ | ✓ | OK |
| OPEN_Q A/D-04 | MASTER 제10조⑤ | 소급회수 한정 | ✓ | ✓ | OK |
| OPEN_Q A/D-14 | MASTER 제4조⑥ | 조직 대리동의 | ✓ | ✓ | OK |
| OPEN_Q A/D-07·08·09 | internal/LAUNCH_GATE_CN·VN·TH | 내부 게이트 | ✓ | ✓ | 수정완료(VN·TH 신규 분리) |
| 부속조항 "제10조" | MASTER 데이터활용 | ✓ | ✓ | OK |
| 부속조항 "제17조·제28조" | 외국법(VN PDPL·PDPA) | N/A | — | 마스터 아님(정상) |

NOTICE 정합: 제7조=controller/processor(D-13), 제8조=위탁·국외이전(외부AI 목록), 제9조=보유기간(D-03). MASTER: 제15조=책임·손배, 제16조=해지·데이터처리, 제10조=데이터활용.

## 3. purpose_code 정합 — DPA·부속 포함

| 문서 | 표기 방식 | 6종 정합 |
|---|---|---|
| CONSENT_SPEC | 코드 토큰(SERVICE_OPERATION 등) | 기준 |
| MASTER 제10조 | ①~⑥ 명칭 | 일치 |
| NOTICE 제3조 | ①~⑥ 명칭 | 일치 |
| PIGOS_B2B_DPA | 역할 매핑(코드 미사용) | **역할표로 매핑 — D-13 확정 시 재검증** |
| ADDENDA 각 제4조 | 목적② 중심 명칭 | 일치 |

DPA는 purpose_code를 직접 쓰지 않으므로 §4 역할 매핑표로 대응. 코드↔명칭 대응은 CONSENT_SPEC §1이 단일 출처.

## 4. 기타 검사
| 검사 | 결과 |
|---|---|
| FINAL·게시가능 표현 | PASS(없음) — 게시여부는 P0 게이트로만 표현 |
| evidence sha256 재검증 | PASS(terms·privacy 일치) |
| 원본 research·evidence 무수정 | PASS |
| 파일 수 | FILE_MANIFEST.md 기준 집계(고객9·내부15·참조2+evidence4·리서치7) |

## 5. 잔여·후속
- ADDENDA COUNSEL NOTES 내 인라인 근거·k수치: 게시 직전 제거(현재 검토용 유지).
- D-13/D-14/D-01/F5의 LEGAL·TECHNICAL 층은 미해소(사람 트랙 — LAWYER_BRIEF·V6~V15·실행게이트 G).
- 신규 결정 D-13·D-14·D-15 등록. VN·TH 출시 게이트 내부문서 분리 완료.

## 변경 이력
| v1.0 | 초판(레지스터·초안 생성) — 수치 폐기 |
| v1.1 | GPT P0 개정 후 12항목 PASS — 층 미분리(폐기) |
| v1.2(본) | 층별 PASS 분리, 교차참조 증거표, purpose_code DPA 포함, FILE_MANIFEST 연동, 낡은 참조 수정 |
