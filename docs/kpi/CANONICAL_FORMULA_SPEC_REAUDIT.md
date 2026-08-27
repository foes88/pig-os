# CANONICAL_FORMULA_SPEC — 재실사 (A ∩ B ∩ B′)

```
실행 스펙  docs/runs/LOOP_OVERNIGHT_D13_REAUDIT.md
Mode      READ-ONLY. 코드·seed·마이그레이션·설정 변경 0
Baseline  e7133fa   (선언 2fedb9c → 문서 5건만 변경돼 재고정, 근거 §0-1)
Machine   bjh
진행      B축 주요 KPI 완료 · A축 부분 · B′축 미착수
```

> **이 문서는 완료되지 않았다.** 실행 스펙 §8 "STOP 시에도 거기까지의 전수표는 남긴다"
> 에 따라 중간 산출물을 남긴다. §8 미추적 목록이 비어야 완료다 — **지금은 비어 있지 않다.**

---

## 0. Status

| 항목 | 값 |
|---|---|
| baseline | `e7133fa` |
| 선언 baseline | `2fedb9c` — `2fedb9c..e7133fa` 는 문서 5건뿐(`api/`·`src/` 0건). 재고정 근거 §0-1 |
| 판정 기준 | `CANONICAL_FORMULA_SPEC.md` §3 — ①코드라인 ②테스트 ③실데이터 수기검산 |
| 시작 시점 상태 | `CONFIRMED 0 · REVOKED 5 · PENDING_RECHECK 2 · AMBIGUOUS 2` |

### 0-1. baseline 재고정 근거

```
git diff --name-only 2fedb9c..e7133fa
  docs/MOBILE_PARITY.md
  docs/kpi/CANONICAL_FORMULA_SPEC.md
  docs/product/COUNTRY_PRODUCT_SPEC_INDEX.md
  docs/runs/LOOP_OVERNIGHT_D13_REAUDIT.md
  handoff/DECISIONS_PENDING_2026-08-27.md

grep -E "^(api|src)/"  →  0건
```

---

## 1. B축 — 응답 필드 → 실제 담기는 산식

> B축을 먼저 돌린 이유(실행 스펙 §7): A축부터 가면 1차와 같은 결과가 나온다.
> `/kpi/trend` 오염을 실제로 잡은 것은 B축 방향이었다.

### 1-1. `DashboardKpi` — 중복 필드는 divergence 가 아니다 ✓

같은 KPI 를 top-level(`psy`/`npd`/`sow_turnover`/`farrowing_rate`)과 일반 맵
`metrics` 두 곳에 담는다. 주석은 "기존 계약 유지를 위해 남긴 중복"이라고만 적혀 있어
**서로 다른 소스일 가능성**을 확인했다.

```python
kpi_service.py:889  ctx.kpi = {**herd, "PSY": psy_value,
                               "NPD": npd_detail.avg_npd, "FARROWING_RATE": farrowing_rate}
kpi_service.py:957  metrics = {**ctx.kpi, "SOW_TURNOVER": npd_detail.sow_turnover}
```

→ **같은 변수에서 온다. divergence 없음.** canonical 값이 `herd` dict 를 덮어쓰므로
top-level 과 `metrics[...]` 가 갈라지지 않는다. 룰엔진 판정값과도 동일 소스다.

### 1-2. ★ PRE_WEANING_MORTALITY — 분모가 **셋**이다

1차 D-13 은 "경로 2개"라고 판정했다. **틀렸다.**

| # | 산식 | 분모 | 위치 | 성격 |
|---|---|---|---|---|
| ① | `deaths / (weaned + deaths)` | `weaned+deaths` | `kpi_service.py:512` | 이벤트 기록 기반 |
| ② | `(born_alive − weaned) / born_alive` | **`born_alive`** | `insight_service.py:229` | 차감 추정 |
| ③ | `deaths / (total_weaned + deaths)` | `weaned+deaths` | `report_service.py:194` | ①과 같은 정의 |
| ④ | `Σ(tb − fw)/tb ÷ n` (복단위 평균) | **`total_born`** | `report_service.py:150,186` | 복별 차감 |
| ⑤ | `(avg_tb − avg_weaned)/avg_tb` (근사) | **`total_born`** | `report_service.py:188-191` | ④의 폴백 |

★ **④·⑤ 는 분모가 `total_born` 이라 사산·미라까지 포함한다.** 즉 "포유폐사율"이 아니라
**"총산 대비 손실률"** 에 가깝다 — 이름과 의미가 어긋난다. `/kpi/trend` 의
"필드명은 npd 인데 값은 WEI" 와 **같은 종류의 오염**이다.

④와 ⑤는 `farrowing_weaned` 인자 유무로 갈린다(`report_service.py:185`). 같은 응답
필드가 호출 방식에 따라 다른 산식을 담는다.

### 1-3. ★ FARROWING_RATE — 산식 **넷**

| # | 산식 | 위치 | 비고 |
|---|---|---|---|
| ① | 코호트 110~150일 전 `mating_number=1`, 115일 내 폐사 제외 | `kpi_service.py:370` | canonical |
| ② | 동기간 `farrowings / matings` | `report_service.py:182` | 서로 다른 개체를 나눈다 |
| ③ | 동월 `farrows_by_month / matings_by_month` | `kpi_service.py:788` (`get_trend`) | 〃 |
| ④ | 동기간 `len(farrowings) / matings_count` | `jobs/kpi.py:138-140` | 〃 |

★ ①의 docstring 이 **"비코호트로 인한 두수변동 왜곡을 제거한다"** 고 명시하는데,
②③④가 정확히 그 비코호트 방식이다. **canonical 이 제거하려던 왜곡이 다른 3경로에 살아 있다.**

### 1-4. ★ PSY — snapshot job 이 다른 분모를 쓴다

| # | 산식 | 분모 | 위치 |
|---|---|---|---|
| ① | `Σweaned(12개월) / AVG(월초 경산 재고)` | 12개월 월초 평균 경산돈 | `kpi_service.py:60-121` |
| ② | `(total_weaned / active) × (365/days)` | **현재 활성 두수(point-in-time)** | `jobs/kpi.py:132-135` |

★ ①의 docstring 은 **"현재 시점 활성두수로 나누면 기간 중 입·퇴출을 반영 못 해 비율이
왜곡됨"** 이라고 적고 그것을 고쳤다고 한다. ②가 정확히 그 방식이다.
그리고 ②는 `parity>=1`(경산) 필터도 없다.

**reachability**: `KpiSnapshot` **reader 가 앱에 0건**이다(모델·잡 외 참조 없음).
따라서 현재는 `LATENT_WRITER` — cron 은 돌지만 아무도 안 읽는다.

> ⚠ **그런데 이것이 안전하다는 뜻이 아니다.** `CLAUDE.md` 설계와 코드 주석 3곳
> (`core/cache.py:8` · `db/keepalive.py:14` · `routers/base/kpi.py:78`)이
> **"근본 해법은 대시보드를 `kpi_snapshots` 조회로 바꾸는 것"** 이라고 적고 있다.
> 그 이관이 실행되면 **대시보드 PSY 가 조용히 ②로 바뀐다.** 지뢰다.

### 1-5. 사산 계열 — 필드명이 다르면 오염이 아니다

| 필드 | 산식 | 위치 | 판정 |
|---|---|---|---|
| `STILLBORN_RATE` | `stillborn / total_born` | `kpi_service.py:523` | 경로① |
| `STILLBORN_RATE` | `(stillborn + mummified) / total_born` | `insight_service.py:211` | 경로② — **오염** |
| `MUMMIFIED_RATE` | `mummified / total_born` | `kpi_service.py:524` | 별도 지표 |
| `stillborn_rate` | `sb / tb_sum` | `report_service.py:195` | 경로①과 같은 정의 ✓ |
| `mummified_rate` | `mum / tb_sum` | `report_service.py:196` | ✓ |
| **`loss_rate`** | `(sb + mum) / tb_sum` | `report_service.py:197` | **경로②와 같은 값이지만 필드명이 다르다 → 오염 아님** ✓ |

★ `loss_rate` 가 좋은 대조군이다 — 합산 정의를 쓰되 **이름이 `stillborn_rate` 가 아니다.**
`insight_service.py:211` 이 문제인 것은 산식이 아니라 **같은 이름을 쓴 것**이다.

### 1-6. B축에서 해소된 것

| 필드 | 결과 |
|---|---|
| `DashboardKpi.metrics` | top-level 과 동일 소스 ✓ |
| `NpdBreakdown.avg_npd` | `calculate_npd` 여집합 ✓ |
| `NpdBreakdown.weaning_to_mating_days` | WEI — **이름이 정확하다** ✓ |
| `ReproductionRow.stillborn_rate` / `mummified_rate` / `loss_rate` | 이름·산식 일치 ✓ |
| `ScorecardRequest.*` | 사용자 입력. 측정 아님 ✓ |
| `KpiTrend.npd` | `5abb8a4` 로 노출 차단됨(값은 WEI) |

---

## 2. A축 — 산식 함수 → 호출자 (부분)

| 산식 함수 | 호출자 | reachability | 근거 |
|---|---|---|---|
| `calculate_psy` | `get_dashboard` · `build_rule_context` | LIVE | `kpi_service.py:846,650` |
| `calculate_npd` | `get_dashboard` · `report_service:325` | LIVE | route `/kpi/npd`, `/reports` |
| `_cohort_farrowing_rate` | `build_herd_kpis:520` · `get_dashboard:817` | LIVE | |
| `build_herd_kpis` | `build_rule_context:650` · `get_dashboard:846` | LIVE | |
| `_avg_active_inventory` | `build_herd_kpis:515` | LIVE | MSY·CULLING·SOW_MORTALITY·REPLACEMENT 분모 |
| `get_trend` | `GET /kpi/trend` | LIVE | `routers/base/kpi.py:112`, 프론트 `kpi.ts:10-12` |
| `insight_service.analyze_*` | `POST /events/*` `_attach_insights` | LIVE | `routers/base/events.py:123,155,250,336` |
| `jobs/kpi.py` 집계 | cron (daily/weekly/monthly) | **LATENT_WRITER** | writer LIVE, reader 0건 |
| `npd_repo.avg_wei_days` | `calculate_npd:238` · `get_trend` wei_rows | LIVE | |
| `scorecard_service` | `POST /scorecard` | LIVE | 입력값 채점(측정 아님) |
| `report_service.*` | `GET /reports/*` | LIVE | 웹 `reports/reproduction/page.tsx:40-44` |

**미완**: `sync_service` 경로에서 KPI 를 계산·반환하는지 미확인.
Codex 는 "sync 에는 insight 부착이 없다"고 했으나 **KPI 값 자체는 확인되지 않았다.**

---

## 3. B′축 — 모바일 DTO 매핑

**미착수.** 실행 스펙 §3 의 완료 기준에 포함된 축이다.

핵심 질문(미해결): 모바일이 하드코딩하는 것이 **라벨인가 산식인가.**
단서 — iOS 가 알림 severity 를 다시 매칭해 색을 낸다(Codex C-4). 서버 판정을 그대로
쓰지 않는 계층이 최소 하나 있고, **값에도 손대는지는 확인되지 않았다.**

---

## 4. 신규 발견 — 1차 D-13 이 놓친 것

| # | 내용 | 심각도 |
|---|---|---|
| N-1 | **PWM 분모가 셋**(`weaned+deaths` / `born_alive` / `total_born`). 1차는 2경로로 판정 | 높음 |
| N-2 | **PWM ④⑤ 는 `total_born` 분모라 사산·미라 포함** — "포유폐사율" 이름과 의미가 어긋남 | 높음 |
| N-3 | **FARROWING_RATE 산식 넷.** canonical docstring 이 "제거한다"고 한 비코호트 방식이 3경로에 살아 있음 | 높음 |
| N-4 | **PSY snapshot job 이 point-in-time 분모** — canonical docstring 이 결함으로 명시한 그 방식. 현재 latent 이나 CLAUDE.md 설계가 이 경로로의 이관을 지시하고 있음 | 중(잠복) |
| N-5 | 같은 응답 필드(`pwmr_b`)가 **호출 인자 유무로 다른 산식**을 담음 (`report_service.py:185`) | 중 |

---

## 5. KPI 별 판정 — ①②③

> 기준: ①코드라인 ②테스트 통과 ③실데이터 수기검산. **하나라도 비면 UNVERIFIED.**

| KPI | ① | ② | ③ | 판정 |
|---|---|---|---|---|
| PSY | `kpi_service.py:60-121` | 미실시 | 미실시 | **UNVERIFIED** |
| NPD | `kpi_service.py:216-256` | 미실시 | 미실시 | **UNVERIFIED** |
| SOW_TURNOVER | `kpi_service.py:234` | 미실시 | 미실시 | **UNVERIFIED** |
| FARROWING_RATE | `kpi_service.py:370-386` | 미실시 | 미실시 | **UNVERIFIED** (+ 산식 4개 미정리) |
| WSI | `kpi_service.py:425-429` | 미실시 | 미실시 | **UNVERIFIED** |
| MSY | `kpi_service.py:559` | 미실시 | 미실시 | **UNVERIFIED** |
| WEANED_PER_LITTER | `kpi_service.py:530` | 미실시 | 미실시 | **UNVERIFIED** |
| 사산 계열 | 위 §1-5 | 미실시 | 미실시 | **AMBIGUOUS** |
| PRE_WEANING_MORTALITY | 위 §1-2 | 미실시 | 미실시 | **AMBIGUOUS** (경로 5개) |

**CONFIRMED 0.** ②③ 을 한 건도 실시하지 않았으므로 승격 가능한 항목이 없다.

---

## 6. ③ 수기 검산 기록

**미실시.** 실행 스펙 §2 가 "이번 런의 핵심"이라고 지정한 항목이다.

---

## 7. Explicit Non-Changes

코드·테스트·seed·마이그레이션·설정 변경 0. 프로덕션 접근 0(이번 회차).
모바일 저장소 접근 0. push 0. 본 문서 1건만 신규 생성.

---

## 8. ★ 미추적으로 남은 것 — **비어야 완료다. 비어 있지 않다**

| # | 항목 | 왜 못 했는지 |
|---|---|---|
| U-1 | **③ 수기 검산 전건** | 프로덕션 SELECT + 손계산 미실시 |
| U-2 | **② 테스트 대조 전건** | KPI 별 대응 테스트 식별·실행 미실시 |
| U-3 | **B′축(모바일 DTO) 전체** | 미착수 |
| U-4 | `sync_service` 의 KPI 값 반환 여부 | 미확인 |
| U-5 | `analytics.py` · `finisher.py:55 mortality()` 계산 프로퍼티 | 미추적 — 응답 모델 안에서 계산하는 형태라 B축 대상 |
| U-6 | DEFERRED 21개 KPI(`ADG`·`FCR`·`RTS_RATE` 등)의 B축 | 우선범주 밖으로 뒀으나 B축은 전수여야 함 |
| U-7 | `alert.py` · `farm.py` · `events.py` · `sync.py` 의 KPI 성 필드 | 스키마 목록만 뽑고 추적 미실시 |

**다음 런은 U-1 부터 시작한다.** ②③ 없이는 어떤 항목도 CONFIRMED 로 갈 수 없다.
