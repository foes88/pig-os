# PigOS — 인수인계 (Claude Code / Codex 전달용)

> 작성: 2026-06-10 · 위치: `C:\dev\PigOS\docs\HANDOFF.md`
> 현재 상태: 자율 플랜 **54/54 완료** · 백엔드 유닛 **219 pass** · **ruff 0 errors** · 프론트 **tsc 0** · 통합테스트 **30 수집**

---

## A. 문서 인덱스 (무엇을 / 어디서 읽나)

| 문서 | 전체 경로 (Windows) | 리포 상대경로 | 용도 |
|------|---------------------|----------------|------|
| 프로젝트 규칙 + 자율 플랜(54/54) | `C:\dev\PigOS\CLAUDE.md` | `CLAUDE.md` | 아키텍처/컨벤션/체크박스 |
| 진행 로그 | `C:\dev\PigOS\PROGRESS.md` | `PROGRESS.md` | 날짜별 완료 내역 |
| 화면·메뉴·상태 스펙 | `C:\dev\PigOS\docs\SCREEN_MENU_SPEC.md` | `docs/SCREEN_MENU_SPEC.md` | UI 권위 문서 |
| 세션 종합 보고서 | `C:\dev\PigOS\docs\AUTONOMOUS_SESSION_REPORT_2026-06-10.md` | `docs/AUTONOMOUS_SESSION_REPORT_2026-06-10.md` | 전체 작업+환경 발견사항 |
| **QA 점검 결과** | `C:\dev\PigOS\docs\QA_REPORT.md` | `docs/QA_REPORT.md` | 계약대조·링크·ruff 결과 |
| **Codex 검증 런북** | `C:\dev\PigOS\docs\CODEX_VERIFICATION.md` | `docs/CODEX_VERIFICATION.md` | 단계별 실행 검증 |
| 다음 단계/로드맵 | `C:\dev\PigOS\docs\NEXT_STEPS.md` | `docs/NEXT_STEPS.md` | 배포+Phase 2 |
| 로컬 개발 가이드 | `C:\dev\PigOS\docs\DEVELOPMENT.md` | `docs/DEVELOPMENT.md` | docker/uv/npm |

---

## B. Codex 에게 (실행 검증 담당)

**읽을 문서**
1. `C:\dev\PigOS\docs\CODEX_VERIFICATION.md` ← 메인(이대로 실행)
2. `C:\dev\PigOS\docs\QA_REPORT.md`
3. `C:\dev\PigOS\docs\AUTONOMOUS_SESSION_REPORT_2026-06-10.md`

**붙여넣을 프롬프트**
```
You are verifying the PigOS repo at C:\dev\PigOS.
Read docs/CODEX_VERIFICATION.md and execute every phase in order on this machine.
Goal: confirm what the Cowork session could NOT run due to sandbox limits —
  (1) integration tests (need Docker Postgres pigos_test),
  (2) frontend Vitest (needs npm install).
Steps:
  0) del .git\index.lock & git reset   (clean the stale lock; commits/worktree are fine)
  1) cd api && uv sync && uv run pytest tests/unit -q        → expect 219 passed
  2) docker compose up -d postgres redis; create DB pigos_test; uv run alembic upgrade head;
     uv run pytest tests/ -q                                  → unit+integration all pass
  3) cd api && uv run ruff check .                            → expect "All checks passed!"
  4) cd src && npm install && npx tsc --noEmit                → 0 errors
  5) cd src && npm i -D vitest jsdom @vitejs/plugin-react @testing-library/react \
       @testing-library/jest-dom @testing-library/user-event && npm test -- --run
  6) Fill the pass/fail table in docs/CODEX_VERIFICATION.md §"합격 종합표".
Report any failure with the exact command + output. Do NOT git push.
```

---

## C. Claude Code 에게 (개발 이어가기 담당)

**읽을 문서**
1. `C:\dev\PigOS\CLAUDE.md` (자율 실행 지침 + 컨벤션)
2. `C:\dev\PigOS\PROGRESS.md`
3. `C:\dev\PigOS\docs\SCREEN_MENU_SPEC.md`
4. `C:\dev\PigOS\docs\QA_REPORT.md` (남은/범위밖 항목)
5. `C:\dev\PigOS\docs\NEXT_STEPS.md` (Phase 2 로드맵)

**붙여넣을 프롬프트 (`cd C:/dev/PigOS && claude` 후)**
```
/loop
CLAUDE.md, PROGRESS.md, docs/QA_REPORT.md, docs/NEXT_STEPS.md 를 읽고 현재 상태 파악.
자율 플랜(54/54)은 완료됨. 이제 QA_REPORT §4(범위 밖)와 NEXT_STEPS §5(Phase 2)에서
다음 우선순위를 위에서부터 구현한다:
  1) /settings/users — 농장 멤버 목록 + 초대 (백엔드 GET farm members + invite 엔드포인트부터)
  2) 대시보드 주간 카운트 집계 API (이번주 교배/분만/이유) + 파이프라인 카드 연결
  3) Addon #1 LLM 실연동: chat 라우터에 use_llm/usage_count 배선 (llm_usage_service.monthly_count)
  4) i18n 점진 전환: 신규 페이지(alerts/settings/reports) 한국어 → messages 키(이미 준비됨) 사용

--- 규칙 ---
- 각 항목: 관련 기존 코드 먼저 읽기 → 구현 → 검증 → 항목별 git commit
- 백엔드: cd api && uv run pytest tests/ -q (그리고 uv run ruff check .)
- 프론트: cd src && npx tsc --noEmit
- 메뉴명/상태/용어는 docs/SCREEN_MENU_SPEC.md 기준
- git push 금지 · 운영DB 직접수정 금지 · 외부 유료 API 호출 금지
지금 바로 시작.
```

---

## D. 공통 주의 (둘 다)
- **stale `.git\index.lock`**: 세션 첫 커밋 잔여물. `del .git\index.lock & git reset` 1회. 커밋/워킹트리는 정상.
- **`git push`는 사람이 직접** (자동 push 안 함).
- 워킹트리에 잡히는 다수 변경(concepts/docs/mvp 등)은 줄바꿈 정규화된 옛 파일 — 이번 작업과 무관.
- 테스트 실행은 **Python 3.12 + uv** 기준. (3.10에선 `datetime.UTC` import 실패)
