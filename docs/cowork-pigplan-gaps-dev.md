# cowork 개발 프롬프트 — PigPlan 갭 채우기 (남은 기능)

> 실행: `cd C:/dev/PigOS && claude --dangerously-skip-permissions`
> 프롬프트: `/loop docs/cowork-pigplan-gaps-dev.md 의 작업을 위에서부터. 각 기능 완료 시 테스트 통과 확인 후 git commit. push 금지.`
> 근거: PigPlan↔PigOS 갭 감사(2026-06-18). 최종 갱신: 2026-06-18.

## 전제(스택)
docker compose up -d postgres redis · alembic upgrade head · seed_e2e · uvicorn:8000 · npm run dev.
테스트: `cd api && uv run pytest tests/ -q` · `cd src && npx tsc --noEmit` · `npm run test:e2e:live`.

## 완료된 것 (재작업 금지)
- ✅ 작업대장(Work Ledger): `GET /events/ledger` + `/reports/ledger` 화면 (백+프+테스트)
- ✅ Alert→Task 자동생성: `task_service.generate_tasks` + `POST /tasks/generate` (이미 존재 — cron만 확인)
- ✅ 이벤트 목록 soft-delete 제외 (버그수정+회귀)

## 작업 (우선순위순)

### [G1] 일일 사육현황 리포트 (PigPlan '일일보고서/daily_report') — P1
- PigPlan 근거: `pigplan_mobile_2023/lib/.../daily_report.dart`(7섹션: 사육/교배/임신/생산/입출/거래/도폐사).
- 백엔드: `GET /farms/{farm_id}/reports/daily?date=YYYY-MM-DD` → 그날의 요약:
  `{ date, herd:{active_sows,gestating,lactating,gilts}, matings, farrowings:{count,total_born,born_alive}, weanings:{count,weaned}, accidents, removals, piglet_deaths }`.
  - 기존 모델 집계(events/removals/sows). 신규 모델 불필요. soft-delete 제외.
- 프론트: `/reports/daily` 날짜 선택 + 섹션 카드. 5개어 i18n. Sidebar 보고서 그룹에 추가.
- 테스트: pytest(픽스처 1일치) + 라이브 E2E 1개.

### [G2] 백신 기록 (PigPlan 'vaccine_record') — P2 (신규 모델)
- 모델 `vaccine_records`(farm_id, sow_id?(null=herd), vaccine_name, lot?, vaccine_date, dose?, notes, deleted_at) + Alembic.
- `POST /farms/{farm_id}/events/vaccines` · `GET ...?sow_id=` (soft-delete 제외).
- 검증: vaccine_date ∈ [sow.entry_date, today], vaccine_name 필수.
- 프론트: /record에 '백신' 탭 추가(기존 패널 패턴). 마스터 백신목록(있으면) 드롭다운.
- i18n 5개어 + 테스트.

### [G3] 관리목표 진행률 (PigPlan 'management_target') — P2
- 농장 목표값(임신/포유/WSI/초교배일령 등 farm_config) vs 실적(kpi_snapshots) 대비.
- `GET /farms/{farm_id}/reports/targets` → `[{metric, target, actual, achieved%}]`.
- 프론트: /reports/targets 진행률 바. (신규 모델 불필요 — config+snapshot 조합)

### [G4] 모돈카드 v2 타임라인 — P2
- `/sows/[id]` 페이지에 산차별 사이클 타임라인(교배→분만→이유) 완성. `GET /reports/sows/{id}/history` 이미 있음 → UI만.

### [G5] LOSS_CALC 경제성 (PigPlan 핵심자산) — P3 (Addon)
- pigplan-rules-extract §2-1 공식: 사산/임신사고/NPD 손실액. 인사이트 `loss` 슬롯에 연결(이미 스키마 있음).
- 농장 단가/육성율 설정 필요 → farm_config 확장. Addon 기능화.

### [G6] 생시체중 필드 — P3 (스키마 확장)
- `farrowing.avg_birth_weight_kg`(있으면) 확인, 없으면 추가 + 검증(0.5~3.5kg). 146지표 ③데이터부족 다수 해소.

## 규칙
- ❌ git push / 운영DB / AWS / 외부유료API / 수치 날조(검증출처만).
- ✅ UI 텍스트 5개어 동시. tsc/pytest 무오류. 각 기능 완료 시 commit + PROGRESS.md.
- ✅ 신규 엔드포인트는 `gen_openapi.py` 재생성 + `docs/mobile-integration-contract.md` 갱신.
- ✅ 라이브 E2E(src/e2e-live) 패턴 재사용(seed 계정·testid·helpers).
