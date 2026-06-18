# cowork 개발 프롬프트 — 모돈 이벤트 갭 채우기 (PigPlan 동등)

> 실행: `cd C:/dev/PigOS && claude --dangerously-skip-permissions`
> 프롬프트: `/loop docs/cowork-sow-events-dev.md 의 작업을 위에서부터. 각 기능 완료 시 테스트 통과 후 git commit. push 금지.`
> 근거: 사용자가 제시한 PigPlan 모돈관리 메뉴 ↔ PigOS 대조. 최종: 2026-06-18.

## 전제(스택)
docker compose up -d postgres redis · alembic upgrade head · seed_e2e · uvicorn:8000 · npm run dev.
테스트: `cd api && uv run pytest tests/ -q` · `cd src && npx tsc --noEmit` · `npm run test:e2e:live`(시드 e2e@pigos.io/e2e!2026pw).

## 설계 원칙 (중요)
- **메뉴 깊게 풀지 말 것.** PigOS는 모바일/현장 우선 → 신규 모돈 이벤트는 **`/record`의 탭으로 추가**(기존 6탭 패턴 재사용: EVENT_TYPES + 패널 + SaveFooter + event-save testid).
- 백엔드는 가능한 **기존 모델 재사용**(새 테이블 최소화). UI 텍스트 5개어 동시. 라이브 E2E 1개씩.
- 신규 엔드포인트 → `gen_openapi.py` 재생성 + `docs/mobile-integration-contract.md` 갱신.

## 완료된 것 (재작업 금지)
- ✅ 교배/분만/이유/사고/도폐사/자돈폐사 탭, 작업대장, 일일보고, 인사이트, 국가KPI, soft-delete.

## 작업 (우선순위순)

### [S1] 양자(Cross-foster) 입력 UI — P1
- 백엔드 이미 있음: `POST /events/piglet_events`의 `event_type=FOSTER_IN|FOSTER_OUT` + `cross_fostering` validator(≤25).
- `/record`에 '양자' 탭 추가(piglet_event 재사용): 방향(IN/OUT) + 두수 + 대상모돈(선택). i18n 5개어 + 라이브 E2E.

### [S2] 모돈 백신 기록 — P1
- **새 테이블 X.** 기존 `HealthEvent`(event_type, drug_code, dose_ml, disease_code, notes) 재사용 → `event_type="VACCINATION"`.
- 엔드포인트 신설: `POST /events/health` · `GET /events/health?sow_id=&type=`(soft-delete 제외). `VaccineCatalog` 마스터로 백신명 드롭다운.
- `/record`에 '백신' 탭. 검증: 백신일 ∈ [입식일, 오늘]. pytest + 라이브.

### [S3] 초발정 기록 노출 — P2
- 백엔드 이미 있음: reproductive `event_type=HEAT_DETECTED`.
- `/record` '사고(repro)' 탭에 묻혀있음 → **'발정/초발정' 별도 탭** 또는 repro 탭에서 HEAT_DETECTED 선택 명확화. 후보돈(GILT) 초발정일 기록 → 초교배 alert 기준에 활용.

### [S4] 모돈 사료급이 기록 — P2
- 기존 `FeedRecord` 모델 존재(엔드포인트 없음). `POST/GET /events/feed?sow_id=` 신설.
- `/record` '사료' 탭(급이량/사료종류/일자). 검증 + i18n + 라이브.

### [S5] 부분이유 기록 — P2
- 현재 전체이유만. Weaning에 부분이유 플래그/잔여두수 처리(스키마 확인 후 최소 확장) 또는 piglet_event로 처리.
- 이유두수 공식 검증과 충돌 없게(부분이유 후 잔여 포유두수 갱신).

### [S6] 모돈 장소이동/농장이동 — P2
- 장소이동(동내): HealthEvent 류 or 신규 `sow_movements`(from_location,to_location,date). 농장이동: TRANSFER 상태 + 이동기록.
- `/record` '이동' 탭. (모델 신설 시 Alembic + 검증)

### [S7] 등지방(Backfat) 측정 — P3
- `sow_measurements`(sow_id, measure_date, backfat_mm, weight_kg?) 신규 or HealthEvent OBSERVATION 활용. 검증(범위).

### [S8] 모돈 그룹 관리 — P3
- `sow_groups`(name, farm_id) + sow.group_id. 그룹별 일괄작업/필터. CRUD 화면.

### [S9] CSV 일괄 업로드 — P3
- `POST /sows/import`(CSV) + `POST /events/import`. 검증 후 일괄 생성, 오류행 리포트. (다운로드는 기존 CSV export 있음)

## 규칙
- ❌ git push / 운영DB / AWS / 외부유료API / 수치 날조.
- ✅ 각 기능: 탭(또는 화면) + 검증 + 5개어 + pytest + 라이브 E2E + commit. OpenAPI/계약서 갱신.
- ✅ 메뉴 통합 유지(깊은 트리 만들지 말 것). 기존 record 탭/패널 패턴 그대로.
