# PigOS 밤새 자율 검증 계획 (per-country E2E)

> 목적: **5개 시장(US/CN/SEA[VN·TH]/LatAm[BR·MX]/KR)마다 회원가입부터 전체 흐름**을 자율적으로 검증 —
> 신규가입→로그인→번식사이클 입력→룰 탐지→국가별 KPI 임계 적용→i18n→리포트→정합성. 발견 이슈는 고치고, 아침에 리포트.
> 실행: 새 세션 `claude --dangerously-skip-permissions` + `/loop` (프롬프트는 §6).

---

## 1. 사전 분석 (이미 확보된 사실)
- **온보딩 8개국** 선택 가능: KR/US/CN/VN/TH/PH/BR/MX → 시장별 farm 생성 가능. (`app/onboarding/page.tsx`)
- **7개 언어**: en/zh/es/vi/th/pt + ko(admin 전용, 고객앱 누수 차단됨).
- **live E2E 인프라**: Playwright `playwright.live.config.ts`(localhost:3000, workers:1) + `e2e-live/helpers.ts`(console/page 에러 추적, gotoApp) + onboarding.live.spec.ts(가입 라운드트립 존재).
- **국가 benchmark 현황**: KR/US/BR/CN/VN 일부 시드, **TH/MX/PH는 글로벌 기본**(`docs/verification/2026-06-24_country_kpi_audit.md` Q1~Q10).
- **룰 40종** + 탐지 파이프라인 검증됨(test_rule_detection_pipeline). pytest 485 baseline.

## 2. 테스트 매트릭스 (시장 × 언어 × KPI)
| 시장 | country | 언어 | 기대 KPI 임계(검증 포인트) |
|---|---|---|---|
| US | US | en | PSY warn 26/crit 23, FARROWING 82/78, CULLING 45/55 |
| KR | KR | ko(admin)+en | PSY 22/18, NPD 35/50, FCR 3.0/3.2(KR전용) |
| LatAm | BR | pt | PSY 28/25, FARROWING 80/70, STILLBORN 8.2 |
| LatAm | MX | es | 글로벌 폴백(MX 시드 없음 — 갭 확인) |
| CN | CN | zh | PSY 24/20, FARROWING 82/78 |
| SEA | VN | vi | PSY 22/18, FARROWING 78/68 |
| SEA | TH | th | 글로벌 폴백(TH 시드 0 — 갭 확인) |

## 3. 시장별 E2E 시나리오 (각 country×lang 1회)
1. **회원가입**: /onboarding → org/farm(country=X) → 계정 생성 → 앱 진입(사이드바 노출).
2. **언어**: 토글로 lang=Y 설정 → 대시보드/메뉴가 Y로 렌더, **원시키 0·크래시 0·ko 누수 0**(고객앱).
3. **번식 사이클 입력**(record): 후보돈 등록 → 교배 → **임신감정(POSITIVE)** → 분만(고사산 6/실산6 = 임계 유발) → 자돈폐사(CRUSHING, 0~3일) → 이유 → 재교배.
4. **룰 탐지 유발**: 위 나쁜 데이터로 stillborn.rate_high·born_alive.low·crushing 등 발화.
5. **viewing/알림 검증**: 대시보드 알림 + `/alerts` + 챗 응답에 해당 rule_id/severity 노출. farm.health_class RED.
6. **국가 KPI 검증**: 같은 데이터라도 country별 임계가 §2대로 적용되는지(예: US PSY warn 26 vs KR 22) — `effective_metric_values` 또는 알림 target_value 대조.
7. **리포트**: reproduction/mortality(사유+일령)/grow-finish/comprehensive-daily 렌더 + 데이터 반영.
8. **정합성**: 잘못된 입력(이유두수 항등식 위반 등) → 422 표시·저장안됨 / `/reports/data-quality` 부정합 0.
9. 로그아웃 → 다음 country.

## 4. 자율 실행 Phase (밤새 /loop)
- **P0 preflight**: docker postgres+redis up · api(8000) up · web(3000) up · `alembic upgrade head` · seed_master/seed_admin. 안되면 띄우고 진행.
- **P1 하네스 구축**: `e2e-live/country-cycle.live.spec.ts` 신규 — §3 시나리오를 country/lang 파라미터로(매트릭스 7행). onboarding 헬퍼 재사용. 데이터 유발은 API 직접 호출 가능.
- **P2 실행+캡처**: 매트릭스 전 행 실행, 행별 pass/fail + 스크린샷 `_uat_tmp/shots/`.
- **P3 국가 KPI 검증 스크립트**: `scripts/verify_country_kpi.py` — 6국 resolve 덤프 + 기대값(§2) 대조 + 갭 표.
- **P4 i18n 누수 스윕**: 7개어 각 로그인+대시보드 SSR에 ko 누수 0 / 원시키 0 / 키감사(1337×7 누락0).
- **P5 정합성**: 422 케이스(분만/이유/교배/양자/비육) + data-quality 0.
- **P6 triage→fix→commit→재실행**: 실패는 원인분석→수정→`git commit`(메시지에 [overnight])→재실행. **막히면 그 지점 기록하고 다음 진행**(멈추지 않음).
- **P7 아침 리포트**: `docs/verification/overnight_<날짜>.md` — 매트릭스 결과표·발견 이슈·수정 커밋·미해결(사람 판단 필요) 목록.

## 5. 가드레일 (밤새 자율 — 반드시 지킴)
- **git push 금지**(커밋만, 사람이 아침에 확인 후 push) · **배포/SSH/AWS 금지** · **외부 유료 API 호출 금지**(LLM Insight는 템플릿 폴백으로 테스트).
- **위조 0**: 데이터 없으면 None/스킵, 임의 KPI값·손실액 생성 금지. TH/MX 갭은 "갭"으로 기록만(임의 시드 금지).
- **타입/린트/테스트 그린 유지**: 각 수정 후 `ruff`·`tsc`·해당 pytest. 회귀나면 즉시 수정.
- **불확실하면 기록 후 진행**, 절대 멈추지 않음. 파괴적 작업(운영DB·삭제) 금지.

## 6. 자율 실행 프롬프트 (새 세션에 그대로 붙여넣기)
```
/loop docs/verification/OVERNIGHT_TEST_PLAN.md 의 계획을 P0부터 순서대로 자율 실행해.
시장별(KR/US/BR/MX/CN/VN/TH) 회원가입→번식사이클→룰탐지→국가KPI검증→i18n→리포트→정합성을
파라미터화한 live E2E(e2e-live/country-cycle.live.spec.ts 신규)로 검증하고,
실패는 원인분석→수정→git commit([overnight] 태그)→재실행. 막히면 기록하고 다음 진행.
가드레일 §5 엄수: push/배포/AWS/유료API 금지, 위조 0, 각 수정 후 ruff·tsc·pytest 그린.
아침에 docs/verification/overnight_<날짜>.md 리포트(매트릭스 결과·이슈·수정·미해결) 작성.
환경: docker postgres+redis + api(8000) + web(3000) 필요(없으면 띄우고 진행).
```

> 비고: P1 하네스(country-cycle spec)가 없으면 먼저 만들고 P2부터 반복. onboarding이 8개국 지원하므로 시장별 가입 가능.
> 국가 benchmark 갭(TH/MX 등)은 이 검증에서 "글로벌 폴백 확인"으로 통과(임계 차등은 시드 추가 후 별도). 갭 목록은 P7 리포트에 명시.
