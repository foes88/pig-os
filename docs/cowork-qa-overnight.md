# PigOS cowork 무중단 QA/검증 (야간)

> 퇴근 후 cowork에 붙여넣어 무중단 실행. `/loop` 없음 — 본문이 연속·순환을 지시.
> **목표: 신규 기능 추가 금지. 기존 코드(특히 인사이트/임계값/알림/디바이스/Task) 검증·버그수정·고정.**
> 실행 전 사람이 1회: `docker compose up -d postgres redis` + `pigos_test` DB + `cd api && uv run alembic upgrade head`.

---

## 프롬프트 본문 (이 아래 전체 복사)

```
PigOS 무중단 QA/검증 모드. 신규 기능 추가 금지. 기존 구현을 검증·버그수정·고정만 한다.
아래 QA 사이클을 순서대로 돌리고, Q8까지 끝나면 다시 Q1부터 더 깊게 순환한다.
사람이 아침에 확인할 때까지 멈추지 말고 이어간다.

═══════════════════════════════════
STEP 0 — 환경 (1회)
═══════════════════════════════════
- CLAUDE.md + PROGRESS.md 읽고 현재 3줄 요약. 최신 main(마지막 b75a4e8 부근).
- DB 점검: docker ps→postgres, 없으면 docker compose up -d postgres redis.
  pigos_test 없으면 생성, cd api && uv run alembic upgrade head.
  uv run pytest tests/unit -q 로 확인 → DB_OK 판정.
- 결과를 PROGRESS.md에 "[야간QA 시작 / DB_OK=?]" 기록·커밋.

═══════════════════════════════════
검증 게이트 (수정 커밋 직전 필수)
═══════════════════════════════════
- 항상: cd api && uv run ruff check → clean / cd src && npx tsc --noEmit → 0
- DB_OK: cd api && uv run pytest tests/ -q → 전부 green
- DB_OK=false: pytest 대신 import-smoke(uv run python -c "import app.main"). 커밋에 [degraded: no-db] 태그.
- i18n: 5개어(en/ko/zh/es/vi) 키 parity 0 (en 기준 누락/초과 0).
- OpenAPI: 라우트 변경 없으면 손대지 말 것. 변경 시 cd api && uv run python scripts/gen_openapi.py 재생성.

═══════════════════════════════════
안전 규칙
═══════════════════════════════════
- 레포 깨진 채로 두지 마라. 게이트 실패+3회 시도 실패 → 미커밋 변경 git restore + PROGRESS에 [BLOCKED] 기록 후 다음으로.
- git push 금지(사람이). 운영DB·AWS·외부 유료 API·.env 실비밀값 금지.
- 위조 금지(통과 안 한 걸 통과로 쓰지 마라). 같은 명령 3회 넘게 반복 금지.
- 새 임계값/시드 숫자를 임의로 만들지 마라(검증된 출처만). 발견한 버그만 고친다.

═══════════════════════════════════
QA 사이클 (순서대로, 버그 발견 시 즉시 수정·커밋)
═══════════════════════════════════

### Q1. 인사이트 "렌더만" 원칙 위반 검사 (최우선)
- src/components/InsightBanner.tsx 에 판정 로직 없는지: threshold 비교, severity 계산,
  confidence 결정이 프론트에 있으면 버그 → 백엔드로 이관. (severity/gap/priority는 백엔드 필드 사용만)
- record 패널이 insights를 그대로 전달만 하는지 확인.

### Q2. 인사이트 엔진 엣지케이스 (api/app/services/insight_service.py)
- total_born=0, born_alive=0, weaned>born_alive(음수 폐사), 임계값 null, 국가행 없음(글로벌 폴백),
  MARKET_PRICE 없음(loss 숨김), top25 없음(relative 숨김) — 각각 예외 없이 안전한지 테스트로 검증.
- analyze_event 실패가 이벤트 입력(이미 커밋)을 깨지 않는지(_attach_insights try/except).
- 부족한 케이스는 tests/integration/test_event_insight.py 에 테스트 추가.

### Q3. 국가별 임계값 해석 정확성
- 우선순위 농장>국가>글로벌이 KR/US/BR/CN/VN 각각 맞는지(insight_service._load_benchmark, threshold_service).
- KR=PigPlan/한돈팜스, US=PigCHAMP 등 source가 올바른 scope에서 나오는지 E2E로 확인.
- 임계값 관리 override→복귀 사이클 무결성(test_threshold_service).

### Q4. 손실/상대 슬롯 정확성
- loss = 손실두수×가격 계산 정확, 가격 없으면 null(금액 표시 금지), 저신뢰/글로벌이면 demo=true.
- relative = top25 대비 gap 부호(above/below) 정확, baseline 없으면 null.

### Q5. 알림/디바이스/Task 회귀 (최근 추가분)
- notification producer savepoint 격리(KPI 실패가 알림생성 막지 않음), 멱등성.
- device 등록 upsert/해제, push_service graceful skip(미설정 시 예외 0).
- task 자동배정 멱등/stale 종료. 각 통합테스트 green 유지.

### Q6. i18n 전수 점검
- 5개어 키 parity 0. 새로 추가된 insights/thresholds 네임스페이스 누락 없는지.
- ICU 보간 변수({value},{threshold},{unit},{n}) 누락/오타 없는지.

### Q7. 계약/스펙 정합성
- docs/api/openapi-v1.yaml 이 라이브 라우트와 일치(gen_openapi 재생성 후 diff 0).
- docs/mobile-integration-contract.md §3에 insights/thresholds 엔드포인트 반영됐는지.

### Q8. 종합 회귀 + 요약
- 전체 pytest + tsc + ruff 재실행. 발견 회귀 즉시 수정.
- PROGRESS.md 갱신: 오늘 한 일 / 발견·수정 버그 / [BLOCKED] / DB재검증 필요 / 다음 추천.

═══════════════════════════════════
순환
═══════════════════════════════════
- Q8까지 끝나면 Q1부터 더 깊게(엣지케이스·적대적 입력·동시성) 다시 순환.
- 새 기능 욕구가 생겨도 추가하지 마라. QA·테스트·문서 정합만 높인다.
- 아침 확인용으로 PROGRESS.md 맨 끝에 "야간QA 결과 요약"을 남겨라.
```

---

## 출발 전 체크 (사람, 1회)
```bash
cd <repo> && git pull
docker compose up -d postgres redis
docker exec pigos-postgres psql -U pigos -c "CREATE DATABASE pigos_test;"  # 없을 때만
cd api && uv run alembic upgrade head && uv run pytest tests/ -q   # green 확인
cd ../src && npx tsc --noEmit
```
> ⚠ cowork와 이 세션이 같은 레포면 **dev 서버 중복 실행 주의**(이전에 next dev 다중 실행으로 .next 잠금 발생).
> cowork는 코드 검증만 하므로 dev 서버를 새로 띄울 필요 없음 — 띄우지 말 것.
