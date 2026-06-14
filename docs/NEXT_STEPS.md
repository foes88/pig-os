# PigOS — 다음 할 일 (Next Steps)

> 작성: 2026-06-10 · 기준: CLAUDE.md 자율 실행 플랜 **54/54 완료** 직후
> 요약: **계획된 개발은 끝.** 남은 건 "내 머신에서 검증 → 배포 → 출시 QA" + 그 다음 로드맵.

---

## 0. 지금 상태 한 줄 요약
- 백엔드 유닛 **219/219**, 프론트 **tsc clean**, 통합테스트 **30개 수집 통과**.
- 코드는 전부 커밋됨(원자적). **`git push`는 안 함** — 내가 직접 확인 후 push.

---

## 1. 복귀 직후 — 검증 (30분, 순서대로)

### 1-1. git 정리 (필수, 1분)
세션 첫 커밋 때 생긴 stale lock 정리 (커밋·워킹트리는 정상, 인덱스만 잠김):
```bat
cd C:\dev\PigOS
del .git\index.lock 2>nul
git reset            REM 인덱스를 HEAD에 맞춤 — git status 깨끗해짐
git log --oneline -15   REM 이번 세션 커밋 확인
```

### 1-2. 백엔드 테스트 (Docker 필요)
```bash
docker compose up -d            # postgres + redis + api
cd api && uv run pytest tests/ -q   # 유닛 219 + 통합 30 전체 실행
```
> 통합 테스트는 샌드박스에 Docker가 없어 이번에 **수집까지만** 검증됨. 여기서 실제 통과 확인.

### 1-3. 프론트 타입체크 + Vitest
```bash
cd src
npx tsc --noEmit
npm i -D vitest jsdom @vitejs/plugin-react @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm test                        # 스캐폴딩된 컴포넌트/페이지 스모크 테스트
```
> Vitest 의존성은 샌드박스 마운트 제약(ENOTEMPTY)으로 설치 못함 → 여기서 설치 후 실행.

### 1-4. 수동 스모크 (브라우저)
- `docker compose up` + `cd src && npm run dev` → http://localhost:3000
- 로그인(test001@pigos.io / 12312300) → 대시보드 / 모돈 / 기록 / **/alerts** / **/reports/reproduction** / **/settings/farm** 클릭 확인.

---

## 2. 검증 통과하면 — 커밋 정리 & push
```bash
git push                        # 검토 후 직접 (자동 push 금지 규칙)
```
> 워킹트리에 줄바꿈 정규화로 잡히는 옛 파일(concepts/docs/mvp 등)은 이번 세션이 만든 게 아님.
> push 전 `git status`로 내 커밋 범위만 올라가는지 확인.

---

## 3. 배포 (MVP 출시, 7/1 목표)

| 대상 | 방법 | 비고 |
|------|------|------|
| 프론트 | Vercel (`src/vercel.json` 준비됨) | env `NEXT_PUBLIC_API_URL` 설정 |
| 백엔드 | `api/Dockerfile`(non-root·healthcheck) + `docker-compose.prod.yml` | AWS 서울(ap-northeast-2) |
| DB 마이그레이션 | `uv run alembic upgrade head` | 신규 `f1a2b3c4d5e6`(llm_usage_logs) 포함 |
| CI | `.github/workflows/ci.yml` | PR→development, 운영배포는 수동 |
| 비밀값 | `.env.example` 참고 — 실제 값은 운영 시크릿으로 | SECRET_KEY/DB/REDIS |

체크: `/health` 200, alembic head 적용, CORS(pigos.io) 확인.

---

## 4. 출시 전 마무리 권장 (선택, 코드 품질)
- **Addon #1 AI Insight 실연동**: `llm_renderer`는 키 없으면 템플릿 폴백. 운영에서 `ANTHROPIC_API_KEY` 넣고 `chat_service`에 `use_llm`/`usage_count` 라우터 배선(현재 기본 template).
- **i18n 실사용 전환**: 신규 페이지(alerts/settings/reports)는 현재 한국어 하드코딩. `messages/*.json`에 키는 추가됨(123키 정합) → 점진적으로 `useTranslations`로 교체.
- **record 페이지 이벤트 인라인 수정 UI**: 현재 삭제+롤백은 모돈 상세에 구현. record 페이지 인라인 편집은 추후.

---

## 5. 그 다음 로드맵 (Phase 2 — MVP 이후, CLAUDE.md 기준)
1. **Task 자동배정 시스템** — Rule Engine 알림 → Task 생성 → 담당자 배정 → 모바일 알림. (`tasks` 테이블 신규)
2. **PRRS 유전자 성과 추적** — `sow.breed` + `health_events.disease_code` 품종별 발생률 분석.
3. **Traceability Addon** — 농장 이벤트 → 도축장 → 소비자 QR 이력 (B2B 데이터 판매).
4. **모바일(Android Native)** — Kotlin/Compose + Room 오프라인 퍼스트 (공용 자산: FastAPI/OpenAPI/sync 프로토콜/KPI 공식/디자인 토큰 이미 준비됨).
5. **pigos.io 랜딩페이지** — 별도 Next.js, en/ko 우선 → zh/es/vi.

---

## 6. 참고 문서
- `docs/AUTONOMOUS_SESSION_REPORT_2026-06-10.md` — 이번 세션 전체 내역 + 환경 발견사항
- `docs/DEVELOPMENT.md` — 로컬 실행 가이드
- `CLAUDE.md` / `PROGRESS.md` — 플랜 체크박스(54/54) + 진행 로그
