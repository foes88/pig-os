# Codex 검증 의뢰 — 인사이트 기능 + 정식환경 후속 (2026-06-17)

> Codex에 그대로 전달. **적대적 교차검증**: "통과한다"를 재현하는 게 아니라 **버그·갭·회귀를 찾는다**.
> 환경: Docker Postgres + Python 3.12+ + 정식 git. 실행 전 `docker compose up -d postgres redis` + `pigos_test` + `cd api && uv run alembic upgrade head`.

---

## 검증 대상 (최근 작업)

### 1) 입력 즉시 분석(Event Insight) 기능 — 신규
- 커밋 범위 대략 `11c7aff`(엔진) ~ `b75a4e8`(#4 임계값 UI).
- 백엔드: `api/app/services/insight_service.py`, `app/schemas/insight.py`, `app/routers/base/events.py`(insights 부착), `thresholds.py`/`threshold_service.py`.
- 프론트: `src/components/InsightBanner.tsx`(순수 렌더러), `src/app/(app)/record/page.tsx`, `src/app/(app)/settings/thresholds/page.tsx`.
- 데이터: `default_metric_values` 메타 5컬럼 + 국가별 시드(US/BR/CN/VN/KR) + MARKET_PRICE_HEAD.

### 2) 정식환경 후속 (이번 세션 A~F)
- `1dbbdd5` sync 교배 검증갭(C), `c25f645` 농장쓰기 RBAC(D), `88199b6` vitest 수정(F), `51c3502` .gitattributes(B).

---

## 적대적 검증 포인트 (반드시 깨보라)

### V1. 인사이트 "렌더 전용" 원칙 (가장 중요)
- `InsightBanner.tsx`에 **판정 로직이 정말 없는가**: severity 계산/threshold 비교/confidence 결정/normalized_gap·priority 산출이 프론트에 있으면 위반.
  → 있으면 보고. (정렬·스타일·i18n 보간만 허용)
- record 패널이 백엔드 `insights[]`를 그대로 전달만 하는가.

### V2. 인사이트 판정 정확성 (백엔드)
- `_severity_from_bench` 방향(above/below) × 경계값(=warning, =critical 정확히 같을 때) off-by-one 검증.
- normalized_gap 부호/분모0 가드, WEANING_AGE LOW/HIGH 양방향이 둘 다 같은 값으로 올바르게 판정되나.
- 국가 우선순위(농장>국가>글로벌): KR 농장이 STILLBORN(글로벌 폴백)·BORN_ALIVE(KR)처럼 **메트릭마다 다른 scope**를 정확히 섞는가. is_global_fallback/source가 선택 scope와 일치하나.
- loss: 가격 없으면 loss=null(금액 표시 0), 저신뢰/글로벌 가격이면 demo=true 인가. 손실두수 음수(이유>생존) 시 손실·경보 안 뜨나.
- relative: top25 없으면 null, gap 부호 above/below 정확한가.

### V3. sync 검증 일관성 (finding #1 + C)
- `_process_mating`의 `_validate_mating_fields`가 REST `MatingCreate`와 **정확히 동일 규칙**인가(mating_type, mating_number 1..5).
- 누락 더 없나: `_process_reproductive`/`_process_piglet`/`_process_health`가 REST 생성경로 대비 빠뜨린 검증(날짜정합·상태전이·FK)이 있나.
- 항목별 reject가 배치 전체를 깨지 않는가(한 항목 VALIDATION_FAILED여도 나머지 accept).

### V4. 농장 RBAC (finding #2 + D)
- `require_farm_role`이 **농장별 role_override**를 보는가(전역 system_role 폴백이 멀티팜에서 오판 안 하나).
- 가드 적용 누락된 farm-scoped mutation이 더 있나(전수): sows/finishers/events/farms/boars/piglets/tasks/members/notifications/thresholds.
- 일상입력(교배/분만/이유 POST)이 워커에게 막히지 않나(과잉 차단 회귀).
- 멀티팜 시나리오: 한 유저가 농장A OWNER·농장B WORKER일 때 B에서 도태 시도 403 되나.

### V5. 회귀·격리
- notification producer savepoint: KPI 집계 실패가 알림 생성을 막지 않는가(트랜잭션 오염 0).
- persist_insights/create_from_alerts 멱등: 재실행 시 미읽음 중복 0.
- period_lock(423), 월마감 후 이벤트 수정/삭제 차단 유지.

### V6. 계약/문서 정합
- `docs/api/openapi-v1.yaml`이 라이브 라우트와 일치(`cd api && uv run python scripts/gen_openapi.py` 후 diff 0).
- `docs/mobile-integration-contract.md`에 insights/thresholds/devices 반영, 오프라인 인사이트 정책 명시.
- i18n 5개어(en/ko/zh/es/vi) parity 0.

---

## 게이트 (검증 중 항상)
- `cd api && uv run pytest tests/ -q` → 320 passed 재현되나 (정식 py3.12+).
- `cd api && uv run ruff check` clean / `cd src && npx tsc --noEmit` 0.
- vitest: `cd src && npm test` (Node 22.12+ 필요; 22.11이면 `NODE_OPTIONS=--experimental-require-module`).

## 보고 형식
- finding마다: 심각도(P0~P2) / 파일·라인 / 재현 / 기대 vs 실제 / 제안.
- "버그 없음"이면 그것도 명시(어디까지 봤는지). 위조 금지.
- 수정은 하지 말고 **보고만**(또는 합의된 P0만 수정). git push 금지.
