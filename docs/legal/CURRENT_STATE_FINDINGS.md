# CURRENT_STATE_FINDINGS v1.0
## PigOS/피그플랜 현행 게시본 발견사항 통합 (2026-07-21 기준)

> 성격: 변호사 검토 전 내부 정리. 근거는 `reference/PIGPLAN_TERMS_SNAPSHOT_v2.0.md`(INTERNAL CANONICAL EVIDENCE SNAPSHOT)와 evidence/ 전문 파일.
> 상태 태그: `LEGAL_REQUIREMENT` `OFFICIAL_GUIDANCE` `DRAFT_GUIDANCE` `CASE_OR_ENFORCEMENT` `INDUSTRY_PRACTICE` `INTERNAL_POLICY_PROPOSAL` `COUNSEL_CONFIRMATION_REQUIRED`

## A. 게시본 자체 결함 (즉시 정비 대상)

| # | 발견사항 | 심각도 | 조치 |
|---|---|---|---|
| F1 | 방침(pigplan.io) 서두 "2019-09-30 시행" vs 하단 "시행일 2026-05-30" 병존 | MED | 개정 이력 조항 형태로 정정 |
| ~~F2~~ **CLOSED** | 방침 제11조 책임자 "진교문/CEO, gyomoon@ezfarm.co.kr(구 도메인)" vs 현 대표 안승환 | MED | **2026-08-25 대표 확인**: 진교문=현 대표이사이며 개인정보 보호책임자 겸임(현행). "안승환"은 구 게시본 footer 오기. 구 도메인만 문제였음 → 연락처는 **조직 메일 `wiselake@wiselake.ai` 로 통일**(2026-08-26 확정 — PIPA §30 은 '연락처'를 요구할 뿐 개인 이메일을 요구하지 않으며, 담당자 변경 시 방침 개정 불요·공개 문서에 개인 이메일 비노출), 담당부서 **경영지원팀** 확정, 전화 +82-31-421-3418 현행 확인. 반영처: publish_candidate(ko·en) · drafts · api/content/legal/privacy_notice.{ko,en}.md. 잔여: CPO 지정 요건(PIPA §31 예외 해당성)은 `COUNSEL_CONFIRMATION_REQUIRED` 유지 |
| F3 | 방침 제1조 수집항목 "이메일" 중복 기재 | LOW | 정정 |
| F4 | 방침·약관이 정보통신망법 중심 인용, "개인정보취급방침" 구용어 | MED | 개인정보 보호법 기준 현행화 |
| F5 | **동의 모델 상충**: pigplan.io(익명화 후 기본 활용·판매+옵트아웃+소급회수 불가 명시) vs pigos.ai("별도 동의한 경우에 한하며", 유상판매·소급회수 미표기) | **HIGH** | 실제 가입 UI·동의 로그 확인(UNVERIFIED) → 게시본·운영 일치화. KR_legal R2 연결 |
| F6 | **pigos.ai/terms는 제목만 "PigOS 이용약관", 본문은 피그플랜 약관 발췌본** (제1~7조 후 제17·18·20·23조로 건너뜀 — 서비스 정의·유료서비스 정의 모두 "피그플랜"). PigOS 실상품(무료 Core, 유료 AI, 크레딧, 조직·농장 계정, PigSignal, 외부 AI 처리, 오프라인 동기화) 미반영 | **HIGH — REPLACE REQUIRED** | PigOS 전용 약관으로 전면 교체 (`PIGOS_MASTER_TERMS_DRAFT.md`). 현행본은 reference only |
| F7 | **약관·방침 페이지가 GoogleAnalytics 컴포넌트를 로드하는데 방침에 쿠키·GA·자동수집정보·해외 분석 수탁자 고지 없음** (terms.astro/privacy.astro에 `<GoogleAnalytics>` import 실물 확인) | **HIGH** | 방침에 자동수집·쿠키·수탁/국외이전 섹션 신설 (`PIGOS_GLOBAL_PRIVACY_NOTICE_DRAFT.md`). `LEGAL_REQUIREMENT`(KR 개인정보 보호법 제30조 기재사항 / EU ePrivacy 쿠키 동의) |
| F8 | pigos.ai 방침 수집항목이 연락처류에 한정 — PigOS 실제 처리 데이터(계정·기기·로그, 생산기록[교배·분만·이유·폐사], KPI·알림, AI 입출력, 업로드 이미지, 동기화 정보, 조직 권한, 결제·크레딧) 미기재 | **HIGH — 전면 재작성** | 글로벌 방침 초안에서 처리 항목 전면 재정의 |
| F9 | 20년 보유 기재 위치 불일치: pigplan.io는 약관 제18조②(비법령 근거 "전국 단위 통계 제공"), pigos.ai는 방침 제5조 표 | MED | D-03 (20년 문구 처리) 결정에 따라 일괄 정리 |

## B. 리서치 산출물 관련 확인사항

- 7개국 리서치의 분석 전제(옵트아웃·유상판매·소급회수 불가·코호트 5·20년)는 게시본 원문으로 전수 확인 — **재실행 불요**.
- GB/EU 문서의 k≥10 / k≥20 / 지배율 70%·85%는 `INTERNAL_POLICY_PROPOSAL` (법령·규제기관 확정 수치 아님. EDPB Guidelines 02/2026은 2026-07-08~10-30 의견수렴 중인 `DRAFT_GUIDANCE`). 확정값은 변호사·통계 검증 후 → `ANONYMIZATION_AND_RELEASE_STANDARD.md`에서 관리.
- 리서치 본문에는 상태 태그가 소급 적용되지 않음 — 후속 산출물(BRIEF·SPEC·초안)에서 태그 체계로 승계하고, 리서치 문서는 pre-counsel research로 지위 고정.

## C. 운영 확인 필요 (문서만으로 판정 불가 — UNVERIFIED)

| # | 항목 | 연결 |
|---|---|---|
| V1 | 실제 가입 플로우의 데이터 활용 동의 UI (체크박스 유무·기본값·문구) 및 동의 로그 존재 여부 | F5, D-01 |
| V2 | 앱 내(모바일/웹앱) 게시 약관이 제3의 버전인지 | 스냅샷 TODO T2 |
| V3 | 2026-05-30 개정 전 구약관 확보 (재동의 범위 판단 기준) | 스냅샷 TODO T3 |
| V4 | PigSignal 기제공 이력 (수신처·범위·계약상 재식별 금지 조항 유무) | 소급회수 조항 방어의 사실 전제 |
| V5 | 콜드 이메일 발송 현황 (KR 포함 — 동의 없는 발송이면 즉시 중단 대상, KR_legal R1 HIGH) | LAWYER_BRIEF |
