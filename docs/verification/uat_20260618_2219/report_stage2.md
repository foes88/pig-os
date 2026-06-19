# UAT 2단계 (갭 보강) 결과 — 2026-06-18

> §9.0 2단계: 사람 지시로 특정 갭만 보강. 새 spec은 `src/e2e-live/_uat_tmp/`에만(격리).
> helpers·기존 10스펙 수정 없음. git commit 없음.

## §9.0이 특정한 갭 3개 처리

### ① §1 언어전환 5개 (ko/en/zh/es/vi) — ✅ PASS (보강 완료)
- 신규 spec: `src/e2e-live/_uat_tmp/i18n-lang-switch.live.spec.ts`
- 방식: NEXT_LOCALE 쿠키를 로케일별로 결정적 세팅 후 reload(앱과 동일 메커니즘) →
  대시보드·/sows에서 `expectNoRawI18nKeys` 0 + 스위처 값이 해당 로케일 반영 확인.
- 결과: **1 passed (20.8s)** — en/ko/zh/es/vi 전부 raw i18n 키 0.
- 시각 확인(§9.8): `shots/dash_ko.png`(전 메뉴 한글), `shots/dash_zh.png`(전 메뉴 중문 + KPI 카드 렌더) 등 10장.
  → 자동 판정 = raw키 0 PASS. **번역 자연스러움/정확도는 사람 최종 판정(SKIP)** — 스크린샷 제공.
- 참고: 첫 시도는 select 조작 + `router.refresh()` 비동기 레이스로 false FAIL → 쿠키 결정적 세팅으로 해결(앱 버그 아님).

### ② §5 손익알리미 — ⏭️ SKIP (미구현 확정)
- `src/app`에 손익/profit-loss/PnL 라우트·화면 없음(확인). 2차 기능.
- **없는 기능은 spec 작성 불가 → 정직하게 SKIP.** (위조 0)

### ③ §6 권한 분기 — ✅ 기존 커버 (추가 불필요)
- `rbac.live.spec.ts`가 이미 OWNER(쓰기버튼 노출) / VIEWER(숨김+읽기전용)를
  `seed_e2e_roles.py`(viewer@/worker@)로 검증 중. 1단계에서 2건 PASS.
- 핵심 권한 분기(쓰기 가능 vs 읽기전용) 커버됨. worker 역할 추가 spec은 한계효용 낮아 보류(원하면 추가 가능).

## 미보강(남은 SKIP, 사람 판단 필요)
- §1 온보딩 위저드(회원가입→농장설정): 가능하나 신규계정 생성·정리 필요. 지시 시 추가.
- §4 KPI badge 색/값 해석, §7 모바일·미관: 시각·해석 판정 → 사람.

## 산출물
- spec: `src/e2e-live/_uat_tmp/i18n-lang-switch.live.spec.ts`
- 스크린샷: `src/e2e-live/_uat_tmp/shots/{dash,sows}_{en,ko,zh,es,vi}.png` (10장)
- run.log: 본 디렉토리 `run.log`(1단계), 2단계 콘솔은 /tmp/uat-lang3.log
- git commit 없음(UAT 규칙). 프로덕션 코드·기존 스펙·helpers 수정 없음.
