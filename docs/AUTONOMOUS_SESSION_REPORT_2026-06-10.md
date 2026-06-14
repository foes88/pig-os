# PigOS 자율 개발 세션 결과 보고서

> 작성: 2026-06-10 (Cowork 자율 세션)
> 베이스: 사용자 체크포인트 `ca429d9` (fixture 수정, 149/149) 이후 이어서 진행
> 범위: CLAUDE.md "자율 실행 플랜" Phase 1부터 순서대로

---

## 1. 한눈에 보기

| 항목 | 결과 |
|------|------|
| 완료 Phase | **Phase 1 (전체) · Phase 2 (P2-1/3/4) · Phase 3 (전체) · Phase 4 (P4-1/4/5)** |
| 백엔드 유닛 테스트 | **188 / 188 통과** (기존 91 → 신규 +97) |
| 프론트엔드 타입체크 | **`npx tsc --noEmit` EXIT 0 (clean)** |
| 신규 백엔드 모듈 | validators 8개, alert_service, alerts router/schema, reproduction rules |
| 신규 프론트 | `/alerts` 페이지, alerts API client, 대시보드 카드, 아이콘 교체 |
| 커밋 방식 | 항목별 원자적 커밋(내 파일만 스테이징), `git push` 안 함 |

검증 원칙: **각 항목 = 구현 → 테스트(green) → 커밋**. 깨진 상태 커밋 없음.

---

## 2. Phase별 상세

### Phase 1 — 이벤트 입력 검증 (Backend Validators) ✅ 전체 완료
신규 폴더 `api/app/validators/`. 모두 순수 함수 → DB 없이 유닛 테스트.

| 태스크 | 내용 | 테스트 |
|--------|------|--------|
| P1-1 | `base.py` — ValidationError(422) 재사용 + 날짜 헬퍼 | — |
| P1-2 | `farrowing.py` — TB≤35, SB/MUM≤25, BA≤TB, 암수합, 체중≤3.0kg | 12 |
| P1-3 | `weaning.py` — 이유두수 항등식 `weaned = nursing-(deaths+out-in)` | 7 |
| P1-4 | `mating.py` — 상태 GILT/OPEN/ACCIDENT + 웅돈 순차 | 9 |
| P1-5 | `cross_fostering.py` — 양자 ≤25/회 | 3 |
| P1-6 | `date_rules.py` — 입식/제거 경계 + 교배·분만·이유 날짜 순서 | 12 |
| P1-7 | `event_service.py` 연결 — 각 이벤트 처리 전 validator 호출 | (통합) |

> 설계 결정: 플랜은 "Pydantic validator + HTTPException(422)"였으나, 기존 코드베이스의
> `app.core.exceptions.ValidationError`(이미 422 핸들러 매핑)를 재사용해 일관성 유지.

### Phase 2 — 모돈 상태 전이 + 알람 (Backend) ✅ P2-1/3/4 완료 (P2-2 기완료)

| 태스크 | 내용 | 테스트 |
|--------|------|--------|
| P2-1 | `validators/sow_state.py` — ALLOWED_TRANSITIONS 전이 강제 | 17 |
| P2-3 | `services/alert_service.py` — 6 과기한 유형 + 3 도태기준, farm_configs 임계값 | 20 |
| P2-4 | `routers/base/alerts.py` + `schemas/alert.py` — GET /alerts/overdue·/cull-candidates, main.py 등록 | (앱 빌드 검증) |

> 설계: 분류 로직을 순수 함수 `classify_overdue`/`classify_cull`로 분리 → DB 없이 유닛 테스트.
> 한계: `sows` 테이블에 생년월일 컬럼이 없어 후보돈 "일령"은 `entry_date` 기준 근사. (보고서 §4 참조)

### Phase 3 — Rule Engine 확장 (Reproduction Rules) ✅ 전체 완료

| 태스크 | 내용 | 테스트 |
|--------|------|--------|
| P3-2 | `Finding.grade` 필드 + `psy_grade` 헬퍼(Excellence/Advanced/Stable/Developing) | 8 |
| P3-1 | `engine/rules/reproduction.py` — wsi.overdue(10/14), rts.rate_high(15/25), pwmr.high(15/20, method A/B) | 9 |
| P3-3 | `tests/unit/test_reproduction_rules.py` — 경계값 | (17 합산) |

> 설계 결정: CLAUDE.md "base.py 하드코딩 완전 제거(DB 벤치마크 기반)" 결정을 존중하여,
> PSY severity는 **벤치마크 기반 유지**하고 4등급은 정보용 `grade` 라벨로 부착.
> reproduction 임계값은 글로벌 기본값이되 `ctx.benchmarks`로 오버라이드 가능하게 설계.

### Phase 4 — 프론트엔드 ✅ P4-1/4/5 완료 (P4-2 기완료, P4-3/P4-6 후속)

| 태스크 | 내용 |
|--------|------|
| P4-1 | `/alerts` 페이지 + `alertsApi` + 타입(OverdueSummary/CullCandidate) + queryKeys + Sidebar 메뉴. 요약카드 6유형 + 도태, 테이블(유형/귀표/상태/경과일/조치→/record 링크), 도태권고 섹션 |
| P4-4 | 대시보드 "관리대상 모돈" 카드 + /alerts 링크 + 도태권고 건수 |
| P4-5 | QuickInputDrawer 이모지 → lucide-react 아이콘(Syringe/Baby/Sprout/AlertTriangle/...) |

> i18n: `/alerts` 본문은 현재 한국어(기존 notifications 페이지와 동일 패턴). Phase 5(P5-1)에서 5개 언어 키화 예정.

---

## 3. 검증 방법 (재현용)

```bash
# 백엔드 유닛 (사용자 머신 권장: Python 3.12 + uv)
cd api && uv run pytest tests/ -q

# 프론트 타입체크
cd src && npx tsc --noEmit
```

이번 세션은 샌드박스(아래 §4) 제약으로 **유닛 레벨(188/188)** + **tsc(clean)** 으로 검증.
통합 테스트(Docker Postgres 필요)는 사용자 머신에서 한 번 더 확인 권장.

---

## 4. 환경에서 발견·우회한 사항 (중요 — 다음 세션 참고)

1. **Python 버전 불일치**: 프로젝트는 3.12 대상이나 Cowork 리눅스 샌드박스는 3.10뿐이고
   GitHub 차단으로 3.12를 받지 못함. → deps를 시스템 python에 설치 + `datetime.UTC`(3.11+)를
   주입하는 **리포지토리 외부 shim**(`/tmp/shim/sitecustomize.py`)으로 3.10에서 전체 유닛 실행.
   **리포지토리는 미변경.** 사용자 머신에선 정상 3.12로 돌아감.

2. **git lock 삭제 불가(Windows 마운트)**: 샌드박스가 `.git` 안 파일을 *생성*은 되나 *삭제*는
   "Operation not permitted". 일반 `git commit`이 자기 lock 정리 실패로 막힘. → 임시 인덱스
   (`GIT_INDEX_FILE`) + `commit-tree` + loose ref 직접 쓰기 헬퍼로 우회(원자적 커밋 유지).

3. **호스트 파일쓰기 간헐적 부분손상**: 호스트 Edit/Write 도구가 이 마운트에서 큰 파일을
   가끔 중간까지만 디스크에 기록(예: event_service.py, QuickInputDrawer.tsx). Read 도구는
   in-context 버전을 보여줘 가려짐. → **모든 파일 쓰기를 샌드박스 직접 쓰기**(git 원본 베이스
   재적용 / cat heredoc)로 전환해 해결. 손상분은 전부 복구·검증 완료.

4. **모돈 생년월일 컬럼 부재**: `sows`에 date_of_birth 없음 → alert_service의 후보돈 "일령"은
   `entry_date` 기준 근사. 정확한 일령이 필요하면 후속으로 컬럼 추가 검토(스펙엔 선택 필드로 존재).

---

## 5. 남은 작업 (로드맵)

> 패턴은 이미 정립됨: validator/서비스는 **순수 함수 분리 → 유닛 테스트**, 라우터는 FarmDep/DbDep,
> 프론트는 useQuery + queryKeys + lib/api/endpoints, 다국어는 5파일 동시.

- **Phase 4 잔여**: P4-3 `/sows/[id]` 번식 이력 타임라인/산차표, P4-6 `/record` 모바일 스택 레이아웃
- **Phase 5 i18n**: P5-1 /alerts 키화, P5-2 상태 용어, P5-3 validator 422 메시지 다국어, P5-4 누락키 점검
- **Phase 6/10 통합 테스트**: conftest DB fixture + E2E (교배→분만→이유), 422 케이스, alert/report 통합 — *Docker Postgres 필요*
- **Phase 7 보고서 API**: 번식/비육 성적(kpi_snapshots 집계), 모돈 이력 엔드포인트, 라우터 등록
- **Phase 8 Settings 프론트**: Farm Config / Benchmarks 페이지
- **Phase 9 누락 화면**: /reports 연동·CSV, /finishers 완성, Sidebar Alerts badge
- **Phase 11 배포**: env 템플릿, vercel.json, Dockerfile 점검, CI — (deploy/ 일부 기완료)
- **Phase 12 CRUD**: 이벤트 수정/삭제 + 상태 롤백, 페이지네이션, CSV
- **Phase 13 프론트 테스트**: Vitest 셋업 + 스모크 테스트
- **Phase 14 Addon LLM**: LLM Renderer + 폴백 + 사용량 로깅 (외부 유료 API 호출은 금지 — 폴백/유닛만)

### 다음 세션 재개 프롬프트
```
CLAUDE.md와 PROGRESS.md 읽고 마지막 완료 항목 확인 후 Phase 4 잔여(P4-3)부터 이어서 진행.
규칙은 CLAUDE.md 자율 실행 지침. 테스트 cd api && uv run pytest tests/ -q, 타입 cd src && npx tsc --noEmit.
```

---

## 6. 이번 세션 커밋 (Phase 2–4, 신규 12; Phase 1은 ca429d9 이전 9커밋)

```
709cb1b docs(phase4): mark P4-1/P4-4/P4-5 complete
096e819 feat(phase4): [P4-5] QuickInputDrawer -> lucide
70e9913 feat(phase4): [P4-4] dashboard overdue card
bb6b547 feat(phase4): [P4-1] /alerts page + API + Sidebar
f011534 docs(phase3): mark P3-1/P3-2/P3-3 complete
fb38621 test(phase3): [P3-3] reproduction rule tests
179881e feat(phase3): [P3-1] reproduction rules
37fc931 feat(phase3): [P3-2] Finding.grade + PSY grade
8370134 docs(phase2): mark P2-1/P2-3/P2-4 complete
b92bc58 feat(phase2): [P2-4] alerts router + schema + register
1f1e8d7 feat(phase2): [P2-3] alert_service
712b3c4 feat(phase2): [P2-1] sow state validator
```

> ⚠️ `git push`는 규칙대로 하지 않았습니다. 사용자 확인 후 직접 push 하세요.
> 워킹트리의 기존 line-ending 정규화 변경(다수 문서/concepts 파일)은 이번 세션이 만든 것이 아니며 손대지 않았습니다.

---

## 7. 추가 진행 (2차 세션 이어서)

> "검증 깔끔한 백엔드부터" 요청에 따라 추가 처리. 환경 리셋으로 shim/헬퍼 재구성 후 진행.

### Phase 7 — 보고서 API (Reports Backend) ✅ 완료
| 태스크 | 내용 | 테스트 |
|--------|------|--------|
| P7-1/2/3 | `services/report_service.py` — 번식(월/분기/연 버킷), 비육(ADG/FCR/폐사율), 모돈 이력(산차 사이클). 순수 빌더 + DB 래퍼 | 11 |
| P7-4 | `schemas/report.py` + `routers/base/reports.py` — `/reports/reproduction·grow-finish·sows/{id}/history`, >2년 400, main.py 등록 | (앱 빌드) |
> 참고: kpi_snapshots 스키마가 얇아(psy/npd/fcr/headcount만) **이벤트 테이블 직접 집계**로 구현.

### Phase 14 — Addon #1 AI Insight (LLM Renderer) ✅ P14-1/2 완료, P14-3 부분
| 태스크 | 내용 | 테스트 |
|--------|------|--------|
| P14-1 | `engine/llm_renderer.py` — 벤더 중립, lazy SDK import, **템플릿 폴백**(키없음/use_llm=False/쿼터초과) | 7 |
| P14-2 | `chat_service.py` — `use_llm`/`usage_count` 파라미터 + `rendered_by` 반환 | (포함) |
| P14-3 | `within_quota` 쿼터 폴백 구현 ✅ / 영속 `llm_usage_logs` 테이블·마이그레이션 **deferred(DB 필요)** | — |
> 외부 유료 API 호출 금지 준수 — 키 없이 폴백 경로만 테스트.

### 2차 누적 검증
- **백엔드 유닛: 206 / 206 통과** (1차 188 → +18: report 11, llm 7)
- 신규 커밋(2차): report_service, reports router/schema, llm_renderer, chat_service + docs

### 갱신된 완료 현황 (자율 플랜 체크박스)
- 완료: **Phase 1·2·3 전체, Phase 4(P4-1/4/5), Phase 7 전체, Phase 14(P14-1/2)**
- 다음 권장: **Phase 8 (Settings 프론트)** — 단, `PATCH /farms/{id}/config`(번식 파라미터 저장) 백엔드
  엔드포인트 신규가 선행 필요. 그 외 Phase 5(i18n)·9·11·12·13은 독립적으로 착수 가능,
  Phase 6·10(통합 테스트)은 Docker Postgres 필요.

---

## 8. 추가 진행 (3차 — Settings/Deploy/i18n)

| Phase | 항목 | 검증 |
|-------|------|------|
| 8 | P8-1 repro config GET/PATCH `/farms/{id}/config/repro` (백) + `/settings/farm` 폼(프론트) | backend unit +8, tsc clean |
| 8 | P8-2 `/settings/benchmarks` 참고표 + 현재값 / P8-3 settings 허브 링크 | tsc clean |
| 11 | P11-1 env 템플릿, P11-2 vercel.json, P11-4 CI workflow, P11-5 DEVELOPMENT.md (P11-3 기존) | JSON/YAML 파싱 OK |
| 5 | P5-4 i18n 키 정합성 — **5개 언어 × 98키 완전 일치** | 스크립트 검증 |

### 3차 누적
- 백엔드 유닛 **214/214**, 프론트 tsc clean
- 완료 Phase: 1·2·3·7 전체, 4(부분), 8 전체, 11(P11-3 포함 사실상 전체), 14(부분), 5(P5-4)

### 남은 항목 & 환경 메모
- **Phase 13 (Vitest)**: 이 샌드박스는 `npm install`(vitest 등)이 마운트 속도로 타임아웃 →
  미설치. 깨끗한 tsc 베이스라인 보호를 위해 config 미추가. **사용자 머신에서**:
  `cd src && npm i -D vitest @testing-library/react @testing-library/user-event @vitejs/plugin-react jsdom @testing-library/jest-dom`
  후 `vitest.config.ts`(jsdom) + `src/tests/setup.ts` 추가 → 스모크 테스트 작성.
- **Phase 6 / 10 (통합 테스트)**: Docker Postgres 필요 → 샌드박스 실행 불가. 코드 작성은 가능.
- **Phase 5 P5-1/2/3**: 신규 페이지(alerts/settings) 하드코딩 한국어를 messages 키로 전환 필요.
- **Phase 4 P4-3/P4-6, Phase 9, Phase 12**: 독립 착수 가능(프론트 tsc / 백 유닛으로 검증 가능).
