# 파일럿 후속 자동실행 플랜 — 계정·조직·UAT·수치검증

> 전제: `import_pigplan.py --farm ALL`로 4농장(2807/4448/848/978) 적재 완료.
> 목적: 실제 운영 시나리오(조직 계층·멀티팜 계정·RBAC)를 구성하고, UAT + 수치 정합성을
> **반복 실행 가능한 스크립트/테스트**로 자동화. 각 Phase는 멱등(재실행 안전).
>
> 실행: `cd api && uv run python -m scripts.<script>` / `uv run pytest tests/pilot/`
> ⚠️ import가 DB 쓰는 중엔 실행 금지(완료 후). 로컬 Docker `pigos` DB 대상.

---

## Phase A — 조직 계층 + 계정 구성  (`scripts/setup_pilot_orgs.py`)

**조직 계층** (organizations: org_type VENDOR<DISTRIBUTOR<DEALER<INDEPENDENT, parent_org_id):
```
VENDOR  "피그플랜 시범사업단"
 └ DEALER "동부지사"  → 농장 2807(용암축산) · 4448(민근/장일)
 └ DEALER "서부지사"  → 농장 848(서해) · 978(무럭이)
```
- 기존 임포트 농장의 organization_id를 위 DEALER로 재배정(2농장씩 묶기).
- 멱등: 조직/계정 고정 UUID, 있으면 skip.

**계정** (users + user_farms):
| 계정 | role / system_role | 접근 농장(기대) |
|---|---|---|
| vendor_admin@pilot | VENDOR_ADMIN | 4농장 전부(서브트리) |
| dealer_east@pilot | DEALER_ADMIN | 2807, 4448 |
| dealer_west@pilot | DEALER_ADMIN | 848, 978 |
| owner_2807@pilot | FARM_OWNER | 2807 |
| owner_4448@pilot | FARM_OWNER | 4448 |
| owner_848@pilot | FARM_OWNER | 848 |
| owner_978@pilot | FARM_OWNER | 978 |
- 초기 비밀번호 고정(`Pilot!2026`) — 테스트 전용, 문서에만 기록(코드 하드코딩 금지, env/상수).
- user_farms.role_override로 농장 멤버십, org 소속으로 상위 접근.

**산출**: 생성 계정·조직·매핑 요약표 출력.

---

## Phase B — UAT 시나리오  (`scripts/uat_pilot.py` — 실 API 왕복)

각 계정으로 **실제 로그인 → 토큰 → 검증** (httpx로 로컬 API 호출):
1. `POST /auth/login` → 200 + system_role 정확.
2. `GET /auth/me` → farm_ids 개수 = 기대치 (owner=1, dealer=2, vendor=4). **RBAC 서브트리 검증**.
3. 접근 농장별 `GET /farms/{id}/kpi/dashboard` → 200 + PSY/NPD 값 존재(0/NULL 아님).
4. `GET /farms/{id}/reports/reproduction?...` → 월별 행 반환.
5. `GET /farms/{id}/alerts/overdue` → 200(과기한 목록).
6. 음성 케이스: owner_2807이 4448 접근 → **403** 확인(격리).

**산출**: 계정×체크 매트릭스(PASS/FAIL) + 실패 상세.

---

## Phase C — 수치 데이터 정합성 테스트  (`tests/pilot/test_reconciliation.py`)

pytest 회귀 스위트(반복 실행):
1. **KPI 대조** (농장×연도): PigOS `calculate_psy` ↔ 피그플랜 raw(Σdusu). 이유두수 오차 = 0 목표, 허용 ≤3%.
   - NPD: PigOS `v_sow_npd` 평균 ↔ raw(교배일−직전이유일) 평균, 허용 ±2일.
   - FR(수태율): PigOS ↔ raw(분만/교배), 허용 ≤3%p.
2. **두수 항등식**: 모든 farrowing에서 total_born = born_alive+stillborn+mummified.
3. **날짜 정합**: 교배<분만<이유 순서 위반 0건. 미래일 0건.
4. **상태 고아**: LACTATING인데 분만이력 없음 = 0.
5. **격리 리포트**: import 시 격리된 이벤트 수/사유 집계(2% 이하 유지).

**산출**: 농장별 정합성 스코어카드(PASS 기준: KPI 오차 ≤3% AND 항등식 위반 0).

---

## Phase D — 원클릭 반복 러너  (`scripts/run_pilot.sh` 또는 make 타깃)

```
A) setup_pilot_orgs.py     # 조직·계정 (멱등)
B) uat_pilot.py            # UAT 매트릭스
C) pytest tests/pilot/     # 수치 회귀
→ 통합 요약 리포트(tests/db/pilot_report_<date>.md)
```
- CI(.github/workflows)에 수동트리거 job으로 등록 가능.
- import 갱신 시 A→B→C 재실행으로 회귀 감시.

---

## 실행 순서 (import 완료 후)
1. `uv run python -m scripts.setup_pilot_orgs`
2. API 기동(`uvicorn app.main:app`) 후 `uv run python -m scripts.uat_pilot`
3. `uv run pytest tests/pilot/ -q`
4. 결과 3종 → `pilot_report_<date>.md` 취합

> 확장: 전 30농가로 스케일 시 이 플랜을 농장리스트만 바꿔 재사용. 조직 계층은
> 실제 총판/대리점 구조(TA_FARM.company_cd/agent_cd)로 매핑 가능(2단계).

---

## Phase E — Codex 독립검증
A~D 완료 후 `pigplan_pilot_codex_verify_prompt.md`를 **Codex에 붙여넣어** 적대적 독립검증
(매핑 정확성·import_mode 안전성·이관 충실도·수치 방법론·RBAC/보안). CRITICAL 0 = 파일럿 통과.
