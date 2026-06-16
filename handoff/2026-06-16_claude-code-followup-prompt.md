# PigOS 후속 작업 프롬프트 (Claude Code · 정식환경)

> cowork 야간 QA가 코드 갭 2건(finding #1·#2)을 수정했으나, 그 검증은 **우회환경**(루트 없이 pgserver + Python 3.10 + `datetime.UTC` 심)에서 돌았다.
> 이 프롬프트는 **정식환경(Docker Postgres + Python 3.12 + 정식 git)** 에서 재검증·마무리하기 위한 것이다.
> 붙여넣는 위치: `cd C:/dev/PigOS && claude` 후 아래 본문 전체 복사.

---

## 프롬프트 본문 (이 아래 전체 복사)

```
PigOS 후속 QA/마무리 모드. 아래를 우선순위대로 진행한다.
기준 브랜치 main, 직전 HEAD는 "1d34e8a docs(qa): finding #2 해소" 부근(야간 cowork 커밋 15개 포함).

═══════════════════════════════════
배경 (cowork 야간에 한 일)
═══════════════════════════════════
- finding #1: 오프라인 /sync 경로가 REST 생성경로의 카운트 검증을 안 거치던 갭 → _process_farrowing/_weaning에 항목별 검증 추가(SyncRejected reason=VALIDATION_FAILED). offline-sync-spec 2-8절 문서화.
- finding #2: 권한 판정이 전역 user.system_role만 봐서 멀티팜에서 농장별 역할 차등 불가 → permissions.effective_farm_role() + dependencies.require_farm_role() 신규, members/thresholds/notifications 라우터 이관.
- 회귀잠금 테스트 다수 추가(test_event_insight, test_threshold_service, test_notification_producer, test_thresholds_perm, test_sync_validation).
- cowork 측 최종: 312 passed (단, pgserver+py3.10+UTC shim 우회환경).

═══════════════════════════════════
안전 규칙 (엄수)
═══════════════════════════════════
- 신규 기능 추가 금지(아래 항목 외). 발견한 버그/갭만 수정. 위조 금지(통과 안 한 걸 통과로 쓰지 마라).
- git push 금지(사람이). 운영DB/AWS/외부 유료 API/.env 실비밀값 금지.
- 새 임계값/시드 숫자 임의 생성 금지(검증된 출처·기존 규칙 미러만).
- 레포 깨진 채 두지 마라. 게이트 3회 실패 시 git restore 후 PROGRESS에 [BLOCKED] 기록하고 다음으로.

═══════════════════════════════════
검증 게이트 (커밋 직전 필수)
═══════════════════════════════════
- docker compose up -d postgres redis  (없으면)
- (최초 1회) pigos_test 생성 + cd api && uv run alembic upgrade head
- cd api && uv run ruff check        → clean
- cd api && uv run pytest tests/ -q  → 전부 green
- cd src && npx tsc --noEmit         → 0
- i18n: src/messages/{en,ko,zh,es,vi}.json 키 parity 0 (en 기준)
- 라우트 변경 시에만: cd api && uv run python scripts/gen_openapi.py 재생성 후 diff 확인

═══════════════════════════════════
작업 (우선순위)
═══════════════════════════════════

### A. [필수] 정식환경 회귀 — cowork 우회환경 결과 재확인
- Docker Postgres + Python 3.12(프로젝트 requires-python>=3.12)에서 `uv run pytest tests/` 전체 실행 → 312 green 재확인.
- 특히 cowork가 추가/수정한 것들이 정식환경에서도 통과하는지:
  - test_sync_validation.py (7), test_thresholds_perm.py::test_per_farm_role_isolation,
    test_event_insight.py(TestEdgeCases/TestRelativeSlotAbove/TestPersistIdempotency),
    test_threshold_service.py(TestRegionPriority), test_notification_producer.py(savepoint 격리)
- 차이(특히 py3.10↔3.12 런타임, datetime.UTC 등)로 인한 실패가 있으면 수정. 없으면 "정식환경 312 green" PROGRESS 기록.

### B. [권장] 라인엔딩 정규화 (.gitattributes 부재)
- 현재 .gitattributes가 없어 리눅스 체크아웃 시 워킹트리 ~100개 파일이 CRLF↔LF로 통째 modified 표시됨.
- `.gitattributes`에 `* text=auto eol=lf` (필요시 *.bat/*.ps1 eol=crlf 예외) 추가 →
  `git add --renormalize .` → **단독 커밋**("chore: normalize line endings (eol=lf)").
- 정규화 커밋은 다른 변경과 섞지 말 것(diff 노이즈 방지).

### C. [감사] 동기화 검증 일관성 (finding #1 확장)
- finding #1은 farrowing/weaning만 적용. 나머지 sync 경로(_process_mating / _process_reproductive / piglet 등)도
  REST 생성경로 대비 누락된 입력검증이 있는지 점검(예: mating_number 음수/과대, 날짜 정합).
- 갭 발견 시 동일 패턴(항목별 SyncRejected reason=VALIDATION_FAILED)으로 수정 + 테스트 추가 + offline-sync-spec 갱신.
- 계약 변경(신규 reason)은 spec 동시 갱신 필수.

### D. [감사] 농장 스코프 쓰기 RBAC 전수
- require_farm_role 미적용인 farm-scoped mutation 엔드포인트 전수(sows cull/delete, finisher 수정, events 등).
- 원칙: 일상 데이터입력(교배/분만/이유 기록)은 FARM_WORKER 허용이 정상. 단 도태·삭제·설정성 변경(thresholds 등)은
  OWNER/MANAGER 한정이 맞는지 확인. 의도와 다르면 require_farm_role 적용 + 권한 테스트 추가.
- 시스템 스코프 전용 엔드포인트는 기존 require_role 유지.

### E. [선택] 동시성·경계 회귀 테스트
- 동일 sync batch 내 중복 id 처리, 동일 이벤트 동시 POST 멱등, report 기간경계(>2년 → 400) 회귀.

### F. [정리] 프론트 테스트 정식 실행
- cowork 샌드박스에선 npm install이 막혀 vitest 미실행이었음. 정식환경에서 `cd src && npm i && npm test` 통과 확인.

═══════════════════════════════════
마무리
═══════════════════════════════════
- 각 항목 완료 시 게이트 통과 후 의미 단위로 커밋(작은 커밋). 끝나면 PROGRESS.md에 "정식환경 후속" 요약 추가.
- finding #2 잔여: 멀티팜에서 system_role은 여전히 전역값(조직롤/레거시 폴백용). 농장권한은 role_override 기준으로 이관됨 —
  추가 멀티팜 시나리오(한 유저 3+ 농장, 조직관리자 교차접근) 회귀가 필요하면 D에 포함.
```

---

## 참고 (cowork 환경 메모)
- cowork는 Docker/py3.12 불가(GitHub 인터프리터 다운로드 차단)라 PyPI `pgserver`로 임시 Postgres를 띄우고 `datetime.UTC` 1개를 심으로 백필해 전체 통합테스트를 실제 실행했다. 정식환경에선 이 우회가 불필요하다.
- 야간 커밋은 모두 LF·특정 파일만 골라 스테이징했다(CRLF churn 오염 회피). 그래서 B(정규화)가 남아 있다.
