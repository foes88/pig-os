# cowork 밤샘 작업 프롬프트 — 생산성적 보고서(PigPlan 동등) + 국가별 KPI 차등 + UI 이모지 정리

> 실행: `cd C:/dev/PigOS && claude --dangerously-skip-permissions`
> 프롬프트: `/loop docs/cowork-reports-overnight.md 의 작업을 위에서부터 순서대로 진행해. 각 태스크 완료 시 테스트 통과 확인 후 git commit. push 금지.`
> 최종 갱신: 2026-06-17

---

## 0. 미션 한 줄

피그플랜 "전체농가 품종별 주요생산성적" 보고서 수준으로 PigOS 생산성적 보고서를 끌어올리고,
**각국(US/CN/SEA/LatAm/KR) KPI 기준값이 달라야 하는 지표를 걸러내어** 국가별로 다르게 보여준다.

---

## 1. 현재 상태 (출발점)

**이미 있는 보고서** (`api/app/routers/base/reports.py`):
- `GET /reports/reproduction?start&end&period` → 번식성적(PSY/NPD/FR/PWMR/RTS 등 월·분기·연 집계)
- `GET /reports/grow-finish?start&end&group_id` → 비육성적(ADG/FCR/폐사율)
- `GET /reports/sows/{sow_id}/history` → 모돈 산차별 이력
- 프론트: `/reports`, `/reports/reproduction`, `/reports/grow-finish`, `/reports/prrs`

**한계**: 지표 수가 적고(약 10여종), 품종(breed)별 분해가 없으며, 국가별 기준값 차등이 약하다.
피그플랜 실데이터 보고서는 **146개 지표 × 품종별**이다.

---

## 2. 레퍼런스 (반드시 먼저 읽기)

| 파일 | 내용 |
|------|------|
| `c:/dev/realtime/전체농가_품종별_주요생산성적_2025.xlsx` | **피그플랜 실데이터 보고서.** long-format: `농가번호\|농가명\|품종코드\|품종명\|지표명\|값`. 15만행 = 농가×품종×지표. **146개 지표명**이 보고서가 보여줘야 할 KPI의 정의 목록(gold standard). |
| `docs/reference/pigplan-rules-extract.md` | 피그플랜 KPI 계산식·규칙 추출본 |
| `docs/specs/2026-03-19_kpi-calculation-specs.md` | PSY/NPD/FCR 엣지케이스 확정 공식 |
| `api/app/db/models/config.py` | `country_configs` / `default_metric_values`(임계값·avg·top25, scope 체인 farm>country>global) |

> xlsx 읽기: `import openpyxl; wb=openpyxl.load_workbook(path, read_only=True, data_only=True)`.
> 한글 콘솔 깨짐 주의 → 결과는 UTF-8 파일로 써서 확인. **146개 지표명 전수**를 먼저 추출해 목록화할 것.

**146지표 카테고리(예시)**: PSY/MSY/LSY/MSY(자돈출하포함), 재귀일 분포(3일내/4~6일/7일내/8·9·10일이상),
교배복수(1·2·3회+재발율), 도태율·도폐사율·폐사율(모돈), 미라율·사산율, 총산·실산·이유두수, 포유/임신일수,
기초·기말 모돈재고, 평균산차, 모돈/웅돈비율, 모돈회전율 등.

---

## 3. 작업 (순서대로)

### [R1] 146지표 매핑 테이블 작성 (분석 — 코드변경 전)
- `docs/specs/2026-06-17_pigplan-metrics-mapping.md` 신규.
- 146지표 각각을 4분류: ① **이미 PigOS가 계산함**(엔드포인트/공식 명시) ② **데이터는 있으나 미집계**(추가 집계로 가능) ③ **데이터 부족**(어떤 이벤트/필드가 더 필요한지) ④ **국가 무관 vs 국가별 차등 필요**.
- 출력: 표 (지표명ko/en, PigOS metric_code, 분류, 계산식 또는 갭, 국가차등Y/N, 근거).
- ⚠️ 수치 임의 생성 금지. 매핑·분류만. 모르면 "③ 데이터부족"으로 표기.

### [R2] 국가별 차등이 필요한 지표 선별 (핵심 요청)
- R1의 "④ 국가별 차등" 행만 모아 `docs/specs/2026-06-17_country-kpi-differences.md` 작성.
- 차등 축: **(a) 기준값/벤치마크**(목표·top25·평균), **(b) 임계값**(warning/critical), **(c) 단위**(kg↔lb), **(d) 정의 자체**(예: 출하일령·이유일령 관습 차이).
- 국가셋: **KR / US / CN / SEA(베트남 등) / LatAm(브라질 등)**.
- 값 출처 규칙(엄격): **KR = 피그플랜 실데이터(위 xlsx) / 검증된 한돈팜스**, US = PigCHAMP, 그 외는 공신력 출처만.
  출처 없는 칸은 **빈칸 + "출처 미확보"** 로 두고 절대 지어내지 말 것. (글로벌 폴백은 `default_metric_values` global scope.)
- 결과를 `default_metric_values`(country scope) 시드 후보로 정리 — 실제 INSERT는 R4에서.

### [R3] 보고서 API 확장 (백엔드)
- 품종(breed)별 분해 추가: `GET /reports/reproduction?...&group_by=breed` → 품종별 행.
- 지표 확장: R1 ①②에 해당하는 지표를 `ReproductionRow`/신규 스키마에 점진 추가(한 번에 146개 X — 우선순위 상위 20~30개부터, 커밋 단위로).
- 신규(선택): `GET /reports/production-summary?start&end&group_by=breed|month` → 피그플랜식 통합표.
- 각 지표 응답에 **해당 농장 country 기준값**(target/avg/top25) 동봉 → 프론트는 비교만(판정 재구현 금지, 기존 인사이트 원칙과 동일).
- 모든 신규 지표는 `docs/specs/.../kpi-calculation-specs.md`에 공식 추가 + unit test(경계값) 동반.

### [R4] 국가별 기준값 시드 (검증된 값만)
- R2에서 **출처가 확보된 값만** `default_metric_values` country scope 시드 SQL/러너로 추가.
- 메타 컬럼 채우기: `confidence, is_proxy, proxy_type, threshold_basis, source_ref`.
- ⚠️ 운영 DB 직접 변경 금지. 마이그레이션/시드 파일 생성까지만(적용은 사람).

### [R5] 프론트 보고서 화면 강화
- `/reports` 품종별 탭/필터 + 국가 기준 대비 컬럼(목표/상위25% 대비 색상).
- CSV 내보내기에 신규 지표·품종 분해 반영.
- i18n: 신규 지표명/문구 **en/ko/zh/es/vi 5개 동시** 추가(누락 금지).

### [R6] 테스트 + 검증
- `tests/integration/test_reports.py` 확장: 품종별 분해, 신규 지표 정확성(픽스처 기반), 국가별 기준값 주입 검증.
- 회귀: 기존 reports 테스트 유지. `cd api && uv run pytest tests/ -q` 전체 green.
- 프론트 `cd src && npx tsc --noEmit` + vitest.

### [R7] 이모지 → 아이콘(SVG) 전면 교체 (UI 품질)
> 현재 UI 곳곳에 허접한 유니코드 이모지(🐷💉🤰🐖🍼🌱🔍🔔🧠🚨⚠ℹ✓ 등)가 박혀 있어 그럴싸하지 않다.
> **프로젝트 표준 아이콘 시스템 = `lucide-react`** (이미 `Sidebar.tsx`가 사용). 이걸로 통일한다.

- **교체 대상 파일**(이모지 검출됨):
  `src/app/(app)/page.tsx`(대시보드 PipeItem 💉🤰🐖🍼🌱 + 🧠 + 🚨⚠ℹ✓), `src/components/Topbar.tsx`(🔍🔔),
  `src/app/(app)/record/page.tsx`(🐷 + QuickInput 등), `src/app/(app)/kpi/page.tsx`, `src/app/(app)/sows/[id]/page.tsx`,
  `src/components/BottomNav.tsx`, `src/components/ui.tsx`.
- **교체 규칙**:
  - 의미 아이콘(검색/알림/경고/심각/정보/완료/AI/번식단계) → `lucide-react` 컴포넌트로. 예:
    🔍→`Search`, 🔔→`Bell`, 🚨/CRITICAL→`AlertOctagon`, ⚠/WARNING→`AlertTriangle`, ℹ/INFO→`Info`,
    ✓→`Check`/`CheckCircle2`, 🧠→`Brain`/`Sparkles`, 💉교배→`Syringe`, 🤰임신→`HeartPulse`(또는 적절),
    🐖분만→`Baby`, 🍼포유→`Milk`, 🌱이유→`Sprout`, 🐷빈상태→`PiggyBank`.
  - 크기/색은 주변 텍스트 토큰에 맞춤(`size={14~16}`, `className="text-..."`). 인라인 이모지가 차지하던 자리와 정렬 유지.
  - **브랜드/로고/일러스트**(픽토그램 성격)는 lucide에 없으면 `public/logos`·`public/icons`의 **SVG 에셋** 사용
    (다운로드 키트: `C:/Users/bjh/Downloads/pigos_mobile_web_icon_package`, `pigsignal_landing_svg_assets` 참고). 없으면 단순 inline SVG 신설.
  - severity→아이콘 매핑은 **한 곳(맵 상수)** 으로 모아 중복 제거(대시보드 `SEVERITY_STYLE`에 icon 컴포넌트 필드 추가 등).
- **검증**:
  - 교체 후 `grep`으로 이모지 잔존 0 확인(위 문자셋). `npx tsc --noEmit` green.
  - 신설 E2E 가드 추가: `src/e2e/` 에 "주요 화면 본문에 유니코드 이모지(picto)가 없다" 스모크 1개(대시보드/record/topbar) — 회귀 방지.
  - 시각 확인은 사람 몫이므로, 교체 전후 대상 목록과 매핑표를 커밋 메시지/PROGRESS에 남길 것.
- ⚠️ 아이콘 의미가 모호하면 임의 교체 말고 **매핑 후보를 주석으로 표기**하고 진행(완전 누락보다 근사 아이콘이 낫되, 오해소지 큰 건 보류 표시).

---

## 4. 절대 규칙 (CLAUDE.md 자율모드 + 보안)

- ❌ `git push` 금지 (사람이 직접). 커밋까지만.
- ❌ 운영/Supabase DB 직접 변경, AWS 리소스 생성, 외부 유료 API 호출 금지.
- ❌ **임계값/벤치마크 수치 임의 생성 금지** — 검증된 출처(피그플랜 실데이터·PigCHAMP 등)만. 없으면 빈칸+"출처 미확보".
- ✅ UI 텍스트는 `src/messages/` **5개 언어 동시** 갱신.
- ✅ 타입/테스트 무오류(`tsc --noEmit`, `pytest`). 막히면 그 지점 명시하고 멈춤(통과 위조 금지).
- ✅ 각 태스크 완료 시 `git commit -m "feat(reports): [R#] ..."`, PROGRESS.md 갱신.

---

## 5. 산출물 (아침에 확인할 것)
1. `docs/specs/2026-06-17_pigplan-metrics-mapping.md` (146지표 4분류 매핑)
2. `docs/specs/2026-06-17_country-kpi-differences.md` (국가별 차등 지표 + 출처)
3. 확장된 reports API + 스키마 + 공식 스펙 + 테스트
4. 국가별 기준값 시드 파일(검증값만)
5. 강화된 `/reports` 화면 + 5개어 i18n + CSV
6. **이모지→lucide/SVG 전면 교체** (R7): 대상 7파일 이모지 잔존 0 + severity 아이콘맵 일원화 + 이모지 회귀 가드 E2E
7. `cd api && uv run pytest tests/ -q` 전체 통과 로그 + `tsc --noEmit` green + `test:e2e:smoke` green
