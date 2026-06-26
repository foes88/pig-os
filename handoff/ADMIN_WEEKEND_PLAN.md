# 주말 자동작업 정리 (프롬프트 생성용) — admin 한글 / 테스트데이터 / 메뉴 DB화 / admin CRUD

> 사용자가 이 정리로 loop 프롬프트를 만든다. 각 항목 = 목표·현재상태·작업·인수조건·DB변경·의존성.
> 공통 가드레일: **dev/staging 전용**(운영 직접변경 금지) / 수치·코드값 임의생성 금지(시드는 출처 명시 or 명백한 더미표시) /
>   테스트 안 한 항목 PASS 금지 / Windows PowerShell / 게이트 PASS마다 1커밋 / git push·운영배포는 사람 / 런로그 누적.
> loop 구조: 순차 게이트(STOP-on-FAIL). 독립 항목은 한 항목 FAIL=그 항목만 STOP·다음 진행, 기존 테스트 회귀=전면정지.

## 현재 상태 (운영 DB 실측 2026-06-26)
- users **1**(admin) / organizations·farms·sows **0** → app·admin 화면이 비어 보이는 건 **데이터가 없어서**(버그 아님)
- master/code **미시드**: disease_codes·vaccine_catalog·medication_catalog·event_definitions·scope_kpi_recommendations = **0** (seed_master 운영 미적용)
- governance 시드됨: kpi_definitions 16 · benchmarks 18 · operational_defaults 29 · default_metric_values 85 · market/region 6/8
- dev migration head: `b8e2c4f60a91` (username) — 운영도 동일(배포됨)

---

## 항목 1 — admin 기본 한글 ✅ (코드 완료, 배포만 남음)
- 상태: `i18n/request.ts` admin 호스트 쿠키없으면 ko 기본 (커밋 c69ed34). **배포하면 라이브.**
- 인수조건: admin.pigos.io 첫 진입 한국어 / 고객앱(app.pigos.io)·로그인은 ko 누수 없음(여전히 기본 en).
- 추가 작업 없음 — 배포 대상에만 포함.

---

## 항목 2 — 테스트 데이터 시드 (주말 자동, 권한별) ★핵심
목표: app·admin이 **실데이터로 채워져** 시연·UAT 가능하게. 관리자 → 농장 → 권한별 계정 → 샘플 운영데이터.

작업 범위:
- **2-1 마스터/코드 시드**: `seed_master`(질병코드·백신·약품·이벤트정의) + scope_kpi_recommendations. (출처 있는 표준 코드, 더미 아님)
- **2-2 계정/권한 매트릭스**: 아이디 기반(username). 최소:
  - `admin` (SUPER_ADMIN, 이미 있음)
  - `owner1` (FARM_OWNER) · `manager1` (FARM_MANAGER) · `worker1` (FARM_WORKER) · `vet1` (VET) · `viewer1` (VIEWER)
  - 각 username/email/비번/role 명시, 멱등(있으면 skip)
- **2-3 농장 시나리오**: 2~3개 농장(예: 일관사육 1, 비육 1, 후보돈 도입 1) + 건물/돈군
- **2-4 운영 데이터**: 모돈 N두(상태분포 GILT/OPEN/PREGNANT/LACTATING) + 번식사이클(교배→분만→이유) + 자돈군 + 비육군 + **사료기록(FCR용)** + 일부 폐사/사고 → KPI·알림·리포트가 실제로 발화
- **2-5 기간**: 최근 6~12개월 분포(스냅샷·트렌드·리포트 검증용)

인수조건(머신 판정):
- 시드 후 `admin/overview` 카운트 > 0 (조직/농장/사용자/모돈)
- 각 role 계정 username 로그인 200 + 권한별 접근(예: VIEWER 입력 403, WORKER 입력 201)
- 대시보드 KPI(PSY/FCR 등) None 아님(데이터로 계산됨)
- 알림(alerts/overdue) 일부 발화, 리포트 행 반환
- 멱등 재실행 안전(중복 0)
- **dev/staging DB에만** (운영 직접 시드 금지 — 운영은 별도 결정)

DB변경: 없음(시드만). 의존성: username 스키마(완료).

---

## 항목 3 — 메뉴 DB화 (나중 대비)
목표: admin/앱 메뉴를 코드 하드코딩(`lib/admin/nav.ts`)에서 DB로 → 코드·메뉴명(i18n)·사용여부·순서·권한 관리.

작업:
- **3-1 테이블** `menus`: `code`(unique)·`name_i18n`(jsonb 7개어)·`path`·`icon`·`parent_code`·`sort_order`·`enabled`(bool)·`scope`(admin|app)·`min_role`·`status`(ready|soon)
- **3-2 시드**: 현재 ADMIN_NAV 7개 + 앱 사이드바 항목을 menus로 이전(값 보존)
- **3-3 API**: `GET /admin/menus`(목록) + `PATCH /admin/menus/{code}`(enabled/순서/이름) — super_admin
- **3-4 프론트**: ADMIN_NAV·Sidebar를 menus API에서 로드(폴백: 코드 기본). enabled=false면 숨김
- **3-5 admin 화면**: 메뉴 관리(토글·순서·이름 편집)

인수조건: menus 시드 후 기존 메뉴 1:1 동일 노출(회귀0) / enabled=false 토글 시 해당 메뉴 숨김 / 7개어 이름 / 테스트.
DB변경: `menus` 테이블 신규(마이그레이션). 의존성: 없음.

---

## 항목 4 — admin 마스터데이터 CRUD (코드성 값 관리)
목표: 이미 DB화된 코드성 테이블을 admin에서 **조회·편집**. (지금 데이터는 DB인데 admin 화면이 없어 안 보임)

대상 테이블 + 화면:
- 질병코드(`disease_codes`) · 백신(`vaccine_catalog`) · 약품(`medication_catalog`) · 이벤트정의(`event_definitions`)
- KPI정의(`kpi_definitions`)·벤치마크(`benchmarks`)·운영임계(`operational_defaults`)·rule_configs — **governance(읽기우선, verified 보호)**
- 국가설정(`market_defaults`/`region_defaults`)·KPI노출(`scope_kpi_recommendations`)

작업:
- **4-1 읽기 API+화면 먼저**(목록/상세) — 전 테이블. (이미 `/admin/governance` 일부 있음 — 확장)
- **4-2 편집**: 마스터 코드(질병/백신/약품/이벤트정의)는 CRUD. governance(benchmark/operational/kpi_def)는 **seed validator 통과 필수**(verified 함부로 변경 금지 — §거버넌스 문서 규칙).
- **4-3 감사**: 모든 변경 AuditLog.

인수조건: 각 테이블 admin 목록 표시(행수 일치) / 마스터 코드 추가·수정·삭제 동작 / governance 편집은 validator 위반 시 차단 / 변경 AuditLog 기록 / 권한 super_admin.
DB변경: 없음(기존 테이블). 의존성: 항목2(마스터 시드돼야 화면에 데이터).

---

## 권장 loop 순서 (의존성 반영)
```
G1 항목2-1 마스터/코드 시드 (disease/vaccine/med/event_def)      → admin/앱에 코드 등장
G2 항목2-2~2-5 계정·농장·운영데이터 시드                          → 카운트·KPI·알림 채워짐
G3 항목4 admin 마스터데이터 조회 화면(읽기)                       → DB값이 admin에 보임
G4 항목3 메뉴 DB화(테이블+시드+API+프론트+관리화면)
G5 항목4 편집 CRUD + 감사
(항목1 admin한글은 배포에만 포함, 코드 완료)
```
- G1~G2가 "데이터 안 보임" 즉효 해결. G3가 "코드성 값 admin 노출". G4·G5는 관리기능.
- 각 게이트: 작업 → 테스트 → 전체 회귀(현재 695 기준) → 커밋. 회귀 깨지면 전면 STOP.

## 가드레일(프롬프트에 넣을 것)
- dev/staging 전용. 운영 시드/배포/push 금지(사람).
- 시드 수치: 표준코드(질병/백신 등)는 출처 명시, 운영 KPI 더미는 "테스트"로 명백히 표시(위조 금지 원칙 유지).
- governance(verified benchmark·operational_defaults)는 seed validator·DB CHECK 우회 금지.
- 기존 테스트(695) 회귀 0. flag USE_GOVERNANCE_BENCHMARKS OFF 유지.
- 멱등 시드(재실행 안전).
