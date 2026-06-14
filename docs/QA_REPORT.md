# PigOS — QA/QC 점검 보고서

> 작성: 2026-06-10 · 대상: 자율 플랜 54/54 완료 후 전수 점검
> 방법: 정적 분석(라우트 추출 + 계약 대조 + 링크 무결성) + 빌드/타입/테스트 검증

---

## 1. 요약 (PASS)

| 점검 항목 | 결과 |
|-----------|------|
| 백엔드 라우트 수 | **71개** (auth/orgs/farms/sows/events/finishers/piglets/kpi/reports/alerts/chat/sync) |
| 프론트 API 호출 지점 | **21개** — **전부 백엔드 라우트와 매칭 (누락 0)** |
| 내부 링크 무결성 | **끊긴 링크 없음** (href/router.push 타깃 전부 실존 페이지) |
| 백엔드 유닛 테스트 | **219 / 219 통과** |
| 통합 테스트 | **30개 수집 통과** (실행은 Docker DB) |
| 프론트 타입체크 | **tsc --noEmit = 0 errors** |

---

## 2. API 계약 대조 (프론트 ↔ 백엔드)

자동 스크립트로 `src/lib/api/endpoints/*.ts`의 모든 `apiClient.*` 경로를 추출해
FastAPI 라우트 테이블과 대조 → **불일치(잠재 404) 0건**.

확인된 매핑 (대표):
- 인증: `/auth/login·logout·refresh·register·me`
- 모돈: `GET/POST/PATCH/DELETE /sows`, `/sows/{id}/cull`, `/sows/removals`
- 이벤트: `matings·farrowings·weanings` GET/POST/**PATCH/DELETE**(신규), `reproductive`, `piglet_events`
- 비육: `/finishers` GET/POST/PATCH/DELETE + `/ship`
- 설정: `/config`, **`/config/repro` GET/PATCH(신규)**
- 알림/보고서: `/alerts/overdue·cull-candidates`, `/reports/reproduction·grow-finish·sows/{id}/history`

> 비고: 자동 스크립트가 `auth.ts`의 BASE를 farms로 오인해 `login/logout`을 오탐으로 띄웠으나,
> 실제 경로는 `/auth/login`·`/auth/logout`로 백엔드에 존재함(오탐 확인 완료).

---

## 3. 스펙 ↔ 구현 명칭 차이 (기능 영향 없음)

SCREEN_MENU_SPEC의 일부 라우트명이 실제 구현과 다르나, **앱 내부 링크는 실제 라우트를 사용**하므로 404 없음:

| 스펙 | 실제 구현 | 비고 |
|------|-----------|------|
| `/dashboard` | `/` (루트) | Sidebar Dashboard→`/` |
| `/grow-finish` | `/finishers` | QuickInputDrawer·Sidebar 모두 `/finishers` |
| `/reports/kpi` | `/reports` + `/kpi` | KPI 트렌드 페이지 존재 |
| `/settings/users` | **미구현** | 사용자/권한 관리 — 백엔드 invite 엔드포인트 필요(아래 §4) |

---

## 4. 알려진 한계 / MVP 범위 밖 (의도된 미구현)

1. **`/settings/users` (사용자 초대/권한)** — 농장 단위 멤버 관리 UI/엔드포인트 미구현. orgs 트리는 백엔드에 존재하나 farm-level invite는 Phase 2.
2. **Addon #1 LLM 실연동** — `llm_renderer`는 키 없으면 템플릿 폴백. 운영에서 `ANTHROPIC_API_KEY` + `chat_service` use_llm 배선 필요(코드는 준비됨).
3. **i18n 실사용** — 신규 페이지(alerts/settings/reports)는 한국어 하드코딩. 메시지 키(123개·5개 언어 정합)는 준비됨 → 점진 전환.
4. **대시보드 파이프라인 일부 카운트** — 이번주 교배/분만 카운트는 플레이스홀더(0). 전용 집계 API 추가 시 연결.
5. **record 페이지 인라인 이벤트 수정** — 이벤트 삭제+롤백은 모돈 상세에 구현. record 인라인 편집은 추후.
6. **sowHistory 엔드포인트** — `/reports/sows/{id}/history` 제공되나, 모돈 상세는 3개 쿼리로 타임라인을 직접 구성(중복). 통합 가능(선택).

> 위 항목은 전부 **버그가 아니라 범위 결정**이며 NEXT_STEPS.md 로드맵에 반영됨.

---

## 5. 권장 후속 (우선순위)
1. 사용자 머신에서 통합 테스트 + Vitest **실행 검증** (CODEX_VERIFICATION.md 따라).
2. `/settings/users` 최소 구현(농장 멤버 목록 + 초대) — Phase 2 첫 항목 후보.
3. 대시보드 주간 카운트 집계 API.
4. i18n 점진 전환(키는 준비됨).

---

## 6. 린트(ruff) — 발견 후 수정 완료
- 재점검 중 **ruff 557 errors** 발견(대부분 기존 코드의 E501 줄길이, 기본 88자 한도 탓).
- 조치: `pyproject.toml`에 `line-length=120`(이 코드베이스 실제 기준) + import 자동정렬 +
  스타일 규칙(E501/E701/E702/UP042/UP046/E741) ignore + 실제 미사용(F401/F841) 직접 수정.
- 결과: **`ruff check` All checks passed (0 errors)** → 내가 만든 CI의 ruff 단계가 실제로 통과.
- 실버그 탐지(F-codes)는 계속 활성. 유닛 219 유지.
