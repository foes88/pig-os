---
name: verify
description: >-
  PigOS 코드 검증 워크플로우. 커밋 직전, diff 리뷰 요청, "검증하자/검증해줘",
  또는 high-stakes 영역(KPI 계산·Rule Engine·farm_id 테넌트 격리·권한·과금·
  인증·Alembic 마이그레이션·모바일 sync 충돌)을 만지는 작업을 시작/마무리할 때
  사용. risk 기반 3티어 판정, 결정론 로직 TDD, 듀얼 리뷰, finding 재검증 절차를 제공.
---

# PigOS Verification Workflow

실측 스택: Backend `api/` = FastAPI + SQLAlchemy(async) + asyncpg(PostgreSQL/TimescaleDB) + Alembic + **uv**. Frontend `src/` = Next.js15 + React19 + TS, **npm** (test 러너 없음). Mobile = React Native + WatermelonDB(LWW). 멀티테넌트 = Shared Schema + `farm_id` row-level.

## 1. 먼저 티어를 정한다 (3축 판정)

모든 변경에 같은 강도를 쓰지 않는다.

1. **Blast radius** — 한 화면(↓) vs 데이터·돈·권한·`farm_id` 격리로 번짐(↑)
2. **Reversibility** — `git revert`로 끝(↓) vs Alembic 마이그레이션/`period_locks` 확정데이터/모바일 sync 상태로 못 되돌림(↑)
3. **Determinism** — 입출력이 명세로 고정(→ TDD 의무) vs 탐색적(→ TDD 면제)

경계:
- KPI 건드리는 UI → 값을 *만드는* 코드(`api/app/engine/`, kpi 잡)면 Strict, *보여주는* 코드만이면 Standard.
- sync refactor → wire 포맷·LWW 충돌해소·`sync_queue`면 Strict, 내부 정리뿐이면 Standard.
- `/api/v1` 응답 형태 변경 → 프론트 타입은 `npm run gen:types`로 OpenAPI에서 자동생성됨. 응답 스키마 변경 = 프론트 계약 변경 → Strict + gen:types 재생성.
- `farm_id`/org hierarchy/membership 격리 경계 → 무조건 Strict.
- **불확실하면 한 단계 올린다.**

| Tier | 무엇을 |
|------|--------|
| **Strict** | §2 풀세트 |
| **Standard** | 관련 테스트 + lint/typecheck + self-review diff. 공유 모듈/공개 API 동작이면 reviewer 1회 |
| **Best-effort** | 카피/스타일/프로토타입. 변경 작게, 아키텍처·과금·데이터모델·권한 손대지 않기, 생략한 검증 명시 |

## 2. Strict 풀세트

### TDD — 결정론 로직에만 의무
KPI 공식(PSY/NPD/FCR/분만·이유율) · Rule Engine 규칙(`api/app/engine/rules/`) · 권한 판정 · 과금/entitlement · sync LWW 충돌. → 실패 테스트 먼저 → `RED 확인 (N fail)` → 최소 GREEN → refactor. commit msg에 인용.
면제(test-after): import/export 탐색, dashboard/admin UI, AI Renderer 프롬프트 실험, 프로토타입.
※ Rule Engine LLM Renderer는 "판단 금지, Rule 결과 변환만" — LLM이 KPI 값/판정을 만들지 않는지 테스트로 고정.

### self-review (commit 전)
변경 파일 read-back + sweep grep(§3) + `docs/specs/` cross-ref + commit msg draft를 실 diff와 대조.

### reviewer — 듀얼은 high-stakes만
인증 / `farm_id`·권한 격리 / Alembic 마이그레이션 / sync 충돌 / KPI·Rule Engine / 과금 → single message에 둘 parallel spawn:
- context-aware reviewer (Critical/Important + 신뢰도 %)
- fresh-context reviewer ("본 commit 외 세션·메모리 정보 주입 금지")
그 외 Strict → context-aware single로 충분.

### 모든 finding 재검증 (FP 차단)
① file:line Read ② grep cross-verify ③ `docs/specs/` cross-ref ④ 이전 commit 처리 여부 → 타당하면 정정 / 부당하면 사용자 반박 보고. AI reviewer 자동 신뢰 금지.

### Decision Gate (AI 단독 결정 금지)
아키텍처 / DB 모델 / Shared-Schema↔schema-per-tenant 전환 / 권한·데이터 가시성 / 과금·플랜·addon / 비즈니스 영향 UX / 제품 포지셔닝 / PigOS↔PigSignal 경계 / 농장 운영 영향 자동화 → 사용자 확인 또는 open decision 기록.
※ 자율 실행 모드라도 위 항목은 단독 결정 금지 — `PROGRESS.md`에 open question 기록 후 다음 태스크로. "최선 판단으로 진행"은 구현 디테일에만.

## 3. Sweep & Commands

```bash
# sweep: 단순 단어 단독, fix 후 재실행 + 잔여 0, commit msg에 실 명령 인용
grep -rn "키워드" CLAUDE.md docs/ api/app/ src/ tests/    # \| 금지, multi-word/markdown 함정 회피

# Backend (api/)
cd api && uv run pytest
uv run ruff check . && uv run mypy app/
uv run alembic upgrade head        # 실 DB 적용은 사람 확인 후

# Frontend (src/) — test 러너 없음
cd src && npm run lint && npx tsc --noEmit
npm run gen:types                  # /api/v1 스키마 변경 후 프론트 타입 재생성
```
프론트 test 러너 부재 → Strict 프론트 로직은 typecheck + reviewer로 보강하거나 Vitest 도입 검토.

## Strict 트리거 경로 (PigOS)
`api/alembic/**` · `api/app/engine/**` · `api/app/**/(auth|billing|permission)*` · `api/app/**/sync*` · `api/app/jobs/kpi*` · `api/app/routers/**`(응답 계약) · `farm_id` 격리 코드.
