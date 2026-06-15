# PigOS 자율 야간 스프린트 (안정성 강화판)

> cowork 전달용. `--dangerously-skip-permissions`로 띄운 뒤 아래 **프롬프트 본문**을 그대로 입력한다.
> `/loop`은 이 환경에 없으므로 사용하지 않는다 — 연속 진행은 본문의 "멈추지 말고 / 순환" 지시가 만든다.

---

## 프롬프트 본문 (이 아래 전체를 복사해 입력)

```
PigOS 자율 야간 스프린트 (안정성 강화판).
이 작업은 한 번에 끝내는 게 아니라, 아래 백로그를 위에서부터 순서대로 처리하고,
N7까지 끝나면 다시 BLOCKED 항목 재시도 + 품질 개선으로 계속 순환한다.
전체는 절대 멈추지 말고, 사람이 아침에 확인할 때까지 작업을 이어가라.

═══════════════════════════════════════
STEP 0 — 환경 자가진단 (반드시 먼저, 1회)
═══════════════════════════════════════
1. CLAUDE.md + PROGRESS.md 읽고 현재 상태 3줄 요약. 최신 main 기준(마지막 커밋 88e6dfa 부근).
2. DB 가용성 점검 → 변수 DB_OK 결정:
   a. docker ps 로 postgres 컨테이너 확인. 없으면 `docker compose up -d` 1회 시도.
   b. pigos_test DB 없으면 1회 생성:
      docker exec pigos-postgres psql -U pigos -c "CREATE DATABASE pigos_test;"
   c. cd api && uv run alembic upgrade head  (실패해도 계속)
   d. uv run pytest tests/unit -q 로 한 번 확인.
   - 모두 OK면 DB_OK=true. 한 번 더 복구해도 안 되면 DB_OK=false (degraded 모드).
3. 진단 결과를 PROGRESS.md 상단에 "[야간스프린트 시작 / DB_OK=?]"로 기록하고 커밋.

═══════════════════════════════════════
검증 게이트 (매 태스크 커밋 직전 필수)
═══════════════════════════════════════
- 항상: cd api && uv run ruff check → clean  /  cd src && npx tsc --noEmit → 에러 0
- DB_OK=true: cd api && uv run pytest tests/ -q → 전부 green
- DB_OK=false(degraded): pytest 대신 `uv run python -c "import app.main"` import-smoke + 새 모듈 import 확인으로 대체.
  이 경우 커밋 메시지에 "[degraded: no-db]" 태그 + PROGRESS에 "DB 복구 후 pytest 재검증 필요" 기록.
- UI 텍스트 변경 시 src/messages/ 의 en/ko/zh/es/vi 5개 동시 수정. 커밋 전 en 기준 키 개수 일치 확인.
- high-stakes(KPI·Rule Engine·farm_id 테넌트격리·권한·Alembic·모바일 sync) 수정 시 verify 스킬 사용.

═══════════════════════════════════════
실패/안전 규칙 (가장 중요)
═══════════════════════════════════════
- 레포를 깨진 채로 두지 마라. 게이트 실패 후 합리적 시도(최대 3회)로 못 고치면:
  → 그 태스크의 미커밋 변경만 `git restore`/`git checkout -- <files>`로 되돌리고,
  → PROGRESS.md에 "[BLOCKED] 태스크ID — 사유/에러요약" 기록 + 커밋,
  → 다음 태스크로 넘어가라. 전체 중단 금지.
- 같은 명령을 3회 넘게 반복하지 마라(런어웨이 방지). 안 되면 우회하거나 보류.
- 위조 금지: 통과 안 한 걸 통과한 것처럼 쓰지 마라. 막힌 지점은 그대로 기록.
- 되돌리기 어려운 변경(데이터 삭제·대형 마이그레이션)은 보수적으로. 임의 대형 Alembic 금지.
- 30~60분마다 PROGRESS.md 체크포인트 커밋.

═══════════════════════════════════════
금지
═══════════════════════════════════════
- git push 금지(사람이 직접). 운영/Supabase DB·AWS·외부 유료 API·.env 실비밀값 금지.
- 완료영역 재작성 금지: 이벤트 PATCH/DELETE 백엔드, 비육돈 수정(P12-3), boars/finishers 페이지네이션,
  notifications API(GET·PATCH read·POST read-all), Sidebar 구조, 모돈 상태 v2, Task 자동배정 서비스/라우터.

═══════════════════════════════════════
백로그 (우선순위 순) — 각 완료 시 git commit "feat(phaseN): [ID] 설명"
끝에 Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
═══════════════════════════════════════

### N1. 알림 영구화 Producer (P12-6 백엔드 완성)
notifications 테이블에 생산자가 없어 비어있음. alert→IN_APP Notification 영구화.
- notification_service.py 에 create_from_alerts(db, farm_id): alert_service.get_overdue_sows +
  get_cull_candidates + KPI 알림 순회 → 농장 멤버(OWNER/MANAGER)별 IN_APP Notification 생성.
  멱등: 같은 (user_id, alert_type, related_entity_id) 미읽음 알림 있으면 재생성 금지.
  related_entity_type/id 채워 클릭 이동 가능하게.
- POST /api/v1/farms/{farm_id}/notifications/generate (require_role OWNER/MANAGER).
- 통합 테스트: 과기한 모돈 fixture → 생성 → 멱등(2회차 0건). (DB_OK=false면 서비스 import-smoke만)

### N2. 웹 알림 페이지 연동 (P12-6 프론트)
- endpoints/notifications.ts 신설(list/markRead/markAllRead) + api.types.ts 타입 + queryKeys.notifications.
- notifications/page.tsx: 실시간 KPI 알림 유지 + 영구 알림 목록 섹션 추가
  (개별 읽음 + 전체 읽음 + 미읽음 필터 + 클릭 시 related_entity 이동 + 더보기).
- Topbar/Sidebar/BottomNav alertCount badge를 unread_count에 연결(기존 prop 경로 확인 후).
- i18n 5개 언어.

### N3. Task 자동배정 + 알림 잡 자동화 (ARQ)
- api/app/jobs/ 에 generate_tasks_job, generate_notifications_job 추가 + worker.py cron 등록
  (tasks 05:30, notifications 06:00). 전 농장 순회. 로깅.
- 테스트(또는 degraded면 import-smoke).

### N4. PRRS 유전자 성과 추적 (Phase 2)
- health_events 테이블/모델 존재부터 확인. 없으면 구현하지 말고 PROGRESS에 "선행 스키마 필요"만 적고 N5로.
- 있으면: sow.breed/genetics_id + disease_code(PRRS) 연결 집계 서비스 +
  GET /api/v1/farms/{farm_id}/analytics/prrs-by-genetics + 테스트.

### N5. 프론트 스모크 테스트 (Phase 13 연장)
- src/tests/ 에 RecentEventsSection / tasks page / reports CSV export 스모크(vitest). npm run test green.

### N6. 법무 문서 검토·보강 — 이용약관 + 개인정보보호 (/legal)
현재 src/app/(app)/legal/page.tsx 는 i18n 키 legal.terms / legal.privacy (각 4개 조항 {h,b}) 사용.
스켈레톤 수준이므로 PigOS 제품 실태에 맞게 검토·확장한다. (법적 효력 주장 금지 — "법무 검토용 초안"으로 처리)
- 제품 맥락 반영: 글로벌 양돈 SaaS, 무료 제공 + 데이터 수집·수익화·농가 배분, 5개 시장(US/CN/SEA/LatAm/KR),
  멀티테넌트(farm_id), 오프라인 sync, AI Insight(LLM) addon.
- 이용약관(terms) 보강 조항 예: 서비스 정의/계정·권한, 구독·무료·유료 addon·과금, 데이터 소유권 vs 사용권,
  데이터 수익화·익명화·농가 배분 고지, 금지행위, 책임제한·보증부인, 준거법·분쟁해결, 해지·데이터 반출/삭제, 변경 고지.
- 개인정보보호(privacy) 보강 조항 예: 수집 항목(계정·농장·기기·위치선택)·수집방법, 이용목적, 제3자 제공·국외이전,
  보관기간·파기, 이용자 권리(열람·정정·삭제·이동), 쿠키/분석, 보안조치, 아동, 책임자·연락처(privacy@pigos.io),
  지역별 고지(GDPR/CCPA/PIPA) 요약. ※ 규정 인용은 "요약·참고"로만, 단정적 컴플라이언스 주장 금지.
- 5개 언어(en/ko/zh/es/vi) 동시 작성, 조항 수·키 구조 동일하게. legal.revised 날짜 갱신.
- 작업 후 docs/ 에 legal-review-notes.md 생성: "보강한 조항 / 변호사 확정 필요 항목 / 지역별 추가 검토 포인트" 요약.
- 검증: tsc(legal 페이지 렌더), 5개 로케일 legal.terms/privacy 길이 동일 확인.

### N7. QA/QC 종합
- 전체 pytest(가능시) + tsc + ruff 재실행. 5개 언어 키 en 기준 전수 비교(누락 0).
- 발견 회귀 즉시 수정 커밋. PROGRESS.md 최종 갱신(완료 체크 / BLOCKED 목록 / DB 재검증 필요 항목).

═══════════════════════════════════════
종료/순환
═══════════════════════════════════════
- N7까지 끝나면 BLOCKED 항목 재시도 → 그래도 막히면 두고, 테스트 커버리지·엣지케이스·i18n 정합성 개선으로 품질을 계속 높여라.
- 아침에 사람이 확인하도록 PROGRESS.md 마지막에 "오늘 한 일 / 막힌 것 / 다음 추천"을 요약.
```

---

## 출발 전 체크리스트 (cowork 머신, 사람이 1회 확인)

```bash
cd <PigOS repo>
git pull                                    # 최신 main (88e6dfa 이상)
docker compose up -d                         # postgres + redis
docker exec pigos-postgres psql -U pigos -c "CREATE DATABASE pigos_test;"  # 없을 때만
cd api && uv run alembic upgrade head
uv run pytest tests/ -q                       # ← green 떠야 정상 출발 (red면 그 원인부터)
cd ../src && npm install && npx tsc --noEmit
```

> DB가 안 떠도 프롬프트는 degraded 모드로 진행하지만, 가능하면 DB green 상태에서 출발하는 게 품질이 가장 높다.
