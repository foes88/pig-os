# 동의 인프라 구현 커버리지 (TERMS_DISPLAY_SPEC §7 ↔ 코드)

> 브랜치 `feat/consent-infra`. **PR 초안 전용 — 배포·게시 금지.** 문구는 전부 DRAFT placeholder,
> 게이팅은 기능 플래그로 잠금. D-01~D-04(조건부 DECIDED) 반영, OPEN 항목은 빈 값/플래그 처리.

## §7 체크리스트 대응

| §7 항목 | 상태 | 구현 위치 |
|---|---|---|
| jurisdiction resolver (국가+US주, 농장 단위) | ✅ | `api/app/services/jurisdiction.py` — 선택국≠농장국 시 더 엄격 법역+counsel, US 주코드(NE/CA/CO·CT/MD) |
| 문서 렌더러 (마스터+방침+부속, notice_version) | ✅ | `api/app/services/terms_renderer.py` + `api/content/legal/manifest.json` + placeholder md 9종 |
| 동의 UI: 필수2체크 / ②고지블록 / ③④⑤토글 / NE서면 / VN⑤미노출 | ✅ | `src/components/consent/ConsentForm.tsx` (plan 기반, 서버가 분기 결정) |
| consent_ledger 테이블 (CONSENT §5 스키마) | ✅ | `api/app/db/models/consent.py` + 마이그레이션 `d4a1b2c3e5f7` (12필드+CheckConstraint) |
| CN 가입차단 / TH·VN 게이트 (플래그 해제 가능) | ✅ | `jurisdiction._GATES` + `resolve(feature_overrides=…)` |
| CA 링크·GPC / UOOM 자동 OFF | ✅ | `StateFlags`(do_not_sell_link, honor_uoom) → plan `auto_off_if_uoom`, UI 강제 OFF |
| 철회·제외 요청 플로우 | ✅ | `consent_service.withdraw` (WITHDRAWN/OBJECTED/EXCLUSION_REQUESTED, append-only) + `src/app/(app)/settings/data/page.tsx` |
| 개정 재고지 배너 + 재동의 | ⚠️ 부분 | notice_version 바인딩·비교 기반 마련. 로그인 시 변경배너/재동의 게이트는 후속 |

## 목적×법역 매트릭스 (CONSENT §2 → 코드)

`api/app/policy/consent_matrix.py` (SSOT). 검증: `api/tests/unit/test_consent_plan.py` (9), `api/tests/integration/test_consent_ledger.py` (8).

- ① SERVICE_OPERATION: CONTRACT, 고지. EU 동의구성 금지 준수.
- ② ANON_AGG_STATS (D-01 분기): KR/US=고지+제외요청, EU/GB/BR=LI+이의권, TH=고지+옵트아웃, VN=옵트인, US-NE=서면옵트인(LB525), CN=HOLD.
- ③④⑤ (D-02): 옵트인 기본 OFF 공통. ⑤ VN 미노출, CN HOLD.
- ⑥ EXTERNAL_AI_PROCESSING: KR/EU/US/BR/TH=위탁+이전 고지, VN/CN=국외이전 별도동의.

## 게이트 (기본 잠금, D-07/08/09 / OPEN)

| 그룹 | 게이트 | 해제 플래그 |
|---|---|---|
| CN | 가입 차단(D-07 HOLD) | `CN_signup` |
| TH | 유료·마케팅 차단(D-09) | `TH_paid` |
| VN | 유료·마케팅 차단(D-08) | `VN_paid` |
| EU/GB/BR | 출시 보류(대리인·SCC OPEN) | `EU_release`/`GB_release`/`BR_release` |

## [하지 말 것] 준수 확인

- ✅ 약관 **문구 하드코딩 안 함** — `content/legal/*.md` DRAFT placeholder, 확정본 파일 교체로 반영
- ✅ 사업조건(크레딧·환불·SLA) 하드코딩 안 함 — master_terms `[OPEN]` 공란
- ✅ DPO/대리인 실명 없음 — privacy notice `[OPEN]` 공란
- ✅ 코호트 k(D-05/06) 등 미결 수치 없음 — 매트릭스는 규칙만
- ✅ 배포·게시 안 함 — 브랜치 작업, `any_draft=true`가 게시 차단 신호

## 미결(OPEN) — 후속

- 영어·현지어 확정 번역본 (렌더러는 `lang_pending`/`lang_gate`로 게이트 신호만)
- EU/UK 대리인, BR SCC, TH/VN 라이선스 — 게이트 플래그 상태로 대기
- 가입 플로우 실제 화면 연결(온보딩 스텝 삽입) — ConsentForm 컴포넌트 준비 완료, 마운트는 후속
- 개정 재고지 배너/강제 재동의 게이트
- 복수 국가 조직(organization) 법역 처리 [COUNSEL]
