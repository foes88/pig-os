# PigOS 약관 패키지 — 변호사 검토 지시서 (LEGAL_REVIEW_INSTRUCTIONS)
## 2026-07-21 · 와이즈레이크(주) / PigOS 글로벌

> **이 패키지의 성격**: 완성 약관의 최종 검토본이 **아니라**, 구조·쟁점·레드라인 검토용 **pre-counsel draft**입니다. 게시 가능 여부가 아니라 "구조가 맞는가 / 어느 조항을 어떻게 고쳐야 하는가"에 대한 판정을 요청합니다.

## 1. 문서 목적과 검토 범위
한국 법인 와이즈레이크가 글로벌 양돈 SaaS **PigOS**(서버: 한국, 무료 Core + 유료 AI, 익명·집계 데이터 PigSignal 유상판매, 데이터 목적 6종)를 출시하기 위한 약관·방침·부속조항 초안입니다. 검토 범위: 글로벌 마스터 약관, 글로벌 개인정보 처리방침, B2B DPA, 국가별 부속조항(US/EU/GB/BR/TH/VN), 익명화·동의 스펙. **완성 문안 교정이 아니라 구조·법적 쟁점·레드라인** 검토를 요청합니다.

## 2. 고객 공개 문서 / 내부 문서 구분
- **고객 공개(게시 대상)**: `PIGOS_MASTER_TERMS_DRAFT`, `PIGOS_GLOBAL_PRIVACY_NOTICE_DRAFT`, `COUNTRY_ADDENDA/ADDENDUM_*`(US·EU·GB·BR·TH·VN), `PIGOS_B2B_DPA_DRAFT`(B2B 기업고객 계약 부속).
- **내부 전용(비공개)**: `internal/INTERNAL_LAUNCH_GATE_CN`(중국 출시 차단 정책), `internal/INTERNAL_US_DATA_BROKER_MEMO`, `DECISION_REGISTER`, `LAWYER_BRIEF`, `OPEN_QUESTIONS`, `CONSENT_AND_DATA_USE_SPEC`, `ANONYMIZATION_AND_RELEASE_STANDARD`, `CROSS_DOCUMENT_VALIDATION`, `CURRENT_STATE_FINDINGS`, `research/`, `reference/`.
- 고객 문서 본문의 `<!-- REVIEW NOTE -->`(HTML 코멘트) 및 하단 "COUNSEL REVIEW NOTES"는 게시 전 제거 대상입니다.

## 3. 버전·작성일·근거
작성일 2026-07-21. 현행 게시본 원문·해시는 `reference/PIGPLAN_TERMS_SNAPSHOT_v2.0`(evidence/*.txt, sha256 기재). 초안은 이 스냅샷 + 7개국 리서치 + 대표 결정(D-01~D-04 조건부 DECIDED) 기반.

## 4. 출처 우선순위
①evidence 전문 ②SNAPSHOT (PIGPLAN_TERMS_SNAPSHOT_v2.0.md) ③리서치의 법령·규제기관 인용 ④리서치의 로펌·2차 자료 ⑤SUMMARY_INDEX ⑥분석자 해석. 상위 우선, 동급 충돌은 OPEN QUESTION.

## 5. 알려진 HIGH BLOCKER (검토 전 최우선 확인)
1. **베트남 목적⑤ 매매 해석** — 초안은 ⑤ 비활성(보수적)이나, 유상 이전이 곧 매매인지 PDPL 제17조 적법이전 요건 충족 문제인지 현지 변호사 확정 필요.
2. **조직 관리자 동의 권한** — 조직이 계약농가·직원의 개인정보 동의(목적③④⑤)를 대신할 수 있는 범위. 마스터 제4조에 한정 조항 신설했으나 유효 요건 확정 필요.
3. **controller/processor 역할** — 처리 유형별 역할이 갈릴 수 있어 B2B DPA를 신설했으나 역할 매핑 확정 필요.
4. GA 사전동의(EU/GB — 구현), 실제 서버·수탁자·보유기간 실측 미완(방침의 "시행 중" 표현 검증 대상).

## 6. 국가별 출시 게이트
KR·US·EU/GB·BR = 법무 정리 후 진행 가능(각 대리인·SCC·주별 확인 조건). TH = 현지 대리인·이전수단 확인 전 유료·마케팅 보류. VN = TIA·라이선스·현지화 확인 전 보류. **CN = HOLD**(진입구조 결정 전 서비스·수집 차단 — `internal/INTERNAL_LAUNCH_GATE_CN`).

## 7. 미첨부 필수 문서 (게시 전 확보)
브라질 ANPD SCC 전문·기입본, 태국 국외이전 계약, EU/UK 대리인 지정서, LIA, DPIA, 베트남 TIA/DPIA, 하위처리자 DPA 실본, US 주별 Schedule 전문, 쿠키 정책, 유료 서비스·환불 정책, SLA, 익명화·릴리스 표준 확정본, DATA_REVENUE_SHARE_POLICY(도입 시).

## 8. 변호사에게 요청하는 답변 형식
각 조항·쟁점에 대해 다음 중 하나로 판정해 주십시오:
`APPROVE` / `APPROVE WITH REDLINE`(수정문안 제시) / `REJECT`(사유) / `LOCAL COUNSEL REQUIRED`(관할) / `BUSINESS DECISION REQUIRED`(대표 결정 사항) / `TECHNICAL VERIFICATION REQUIRED`(운영·개발 실측 사항).

## 9. 조문별 승인 상태
현재 전 조문 = DRAFT. 대표 조건부 승인은 설계 방향(D-01~D-04)뿐이며 문안 승인 아님. 회신은 `LAWYER_BRIEF`의 질의 번호(30건)에 연결해 주시면 `DECISION_REGISTER`·`OPEN_QUESTIONS`로 매핑합니다.

## 10. 번역·현지화 상태
현재 전 문서 국문. 법적 우선본 언어(US·GB=영어, TH=태국어, VN=베트남어, BR=포르투갈어)는 확정 후 전문 번역+현지 감수 예정. 기계 번역본을 법적 우선본으로 사용하지 않습니다.

## 11. 제품·인프라 실측 필요 항목 (운영팀)
실제 무료/유료 기능 경계, 크레딧 만료·환불, 수익 배분 여부, 사용 벤더 전체(서버·CDN·PG·푸시·외부 AI), 데이터 저장 국가, 실제 보유기간, 사용자 권한 모델, 익명화 배치·릴리스 절차. → 방침·DPA의 [V] 플래그 항목.

## 12. 게시 전 최종 체크리스트
- [ ] 변호사 판정(§8) 전 조항 수령 및 REDLINE 반영
- [ ] HIGH BLOCKER 4건 해소
- [ ] 대리인·DPO·SCC 등 [OPEN] 실값 확보
- [ ] 운영 실측(§11) 완료 및 방침 [V] 항목 확정
- [ ] REVIEW NOTE·COUNSEL NOTES 제거, 내부문서 분리 확인
- [ ] 국가별 게이트 해제 확인, CN 차단 유지
- [ ] 번역·현지 감수 완료
- [ ] GA 사전동의 등 구현 완료
- [ ] 최종 교차검증(CROSS_DOCUMENT_VALIDATION) PASS

## 부록: 최우선 변호사 질의 (요약 — 상세는 LAWYER_BRIEF 30건)
목적② 국가별 lawful basis / 브라질 SCC 당사자·편입 / 태국 이전수단·대표·DPO·삭제기한 / 베트남 목적⑤·Data Law 라이선스 / 미국 LB525 전자동의·시행범위 / 조직의 농가·직원 대리 동의 범위 / 책임제한·회원면책·소비자 강행법 / 국가 판정기준·준거법.
