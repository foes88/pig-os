# Country Product Spec — BR (브라질)

> **v0.4** · 2026-08-21 · SSOT
> 이 문서와 `api/app/db/br_pilot_seed.py` 는 같은 값을 말해야 한다.
> seed 게이트(G1~G4)가 둘의 불일치를 테스트로 막는다.

---

## 0. 이 문서의 위치

```
country_kpi_policy        어떤 KPI 를 써도 되는가 / 어느 군인가   (거버넌스)
country_kpi_presentation  뭐라 부르고 몇 번째인가                (표현)
이 문서                    위 두 테이블에 무엇을 넣을지의 근거      (제품 결정)
```

**위조 0**: 확정되지 않은 현지 명칭은 넣지 않는다. UNVERIFIED 로 남기고 카드는 공용 라벨을 쓴다.

---

## 1. Full product target (7)

BR 최종 목표 표시 KPI. v0.2 에서 확정된 목록이며 본 개정에서 **변경하지 않았다**.

```
PSY
FARROWING_RATE
BORN_ALIVE
PWMR
NPD
STILLBORN_RATE
FCR
```

---

## 2. BR Pilot v1 — visible subset (3)

파일럿 1차에서 실제로 화면에 노출할 KPI.

| 순서 | kpi_code | 현지 명칭 | 근거 |
|---|---|---|---|
| headline | `PSY` | Desmamados por fêmea/ano | v0.2 확정 |
| 20 | `FARROWING_RATE` | Taxa de Parto | v0.2 확정 |
| 30 | `NPD` | Dias Não Produtivos | v0.2 확정 |

headline 은 `priority_class='NORTH_STAR'` 로 표현한다(`uq_ckp_north_star` 가 국가당 1개 강제).

### 2.1 full target 4개를 Pilot v1 에서 뺀 이유

각 항목은 제품 판단이 아니라 **현재 시스템 제약**이다. 제약이 풀리면 순차 편입한다.

| kpi_code | 제약 | 해소 조건 |
|---|---|---|
| `BORN_ALIVE` | ~~페이로드에 값 없음~~ **해소됨**(`1d07768` metrics 맵) → 남은 제약은 **현지명 미확정** | 포르투갈어 명칭 확정 + D-10-2 확대 결정 |
| `PWMR` | 〃 | 〃 |
| `STILLBORN_RATE` | 〃 (+ 정의 상이로 외부 벤치마크 무효, GLOBAL 에서 `benchmark_exposure='NONE'`) | 〃 |
| `FCR` | 유료 애드온 — `require_addon("ADDON_FCR")`. Entitlement Matrix 결재 대기 상태에서 무료 파일럿에 노출 불가 | Entitlement Matrix 승인 |

visible 로 지정만 하고 값이 없으면 카드가 그려지지 않고 프론트가 `kpi_presentation_unknown_code`
로 관측만 한다. 즉 "정책엔 있는데 화면엔 없는" 상태가 되므로 **지정하지 않는다.**

### 2.2 `SOW_TURNOVER` 는 Pilot v1 에서 제외(HIDDEN)

- v0.2 full target 에 없다. 대시보드가 값을 주고 프론트 레지스트리에도 있지만 **BR Spec 상의 근거가 없다.**
- 현지 명칭 **UNVERIFIED** — 임의 번역을 넣지 않는다.
- 따라서 BR 에서는 explicit `HIDDEN`. 편입하려면 이 문서를 먼저 개정해야 한다.

> ⚠️ 운영 영향: BR 농장 대시보드 카드가 **4장 → 3장**으로 줄어든다. 정책이 의도적으로 숨긴 결과다.

---

## 3. Seed 원칙 — OPTION A (explicit visible / explicit hidden)

```
BR COUNTRY scope 에서 GLOBAL 정책을 암묵 상속해 화면 KPI 가 늘어나게 하지 않는다.

BR 이 표시할 KPI      → explicit visible (PRIMARY)
BR 이 표시하지 않을 KPI → explicit HIDDEN

UI visibility 는 정책 데이터가 결정한다.
프론트 레지스트리에 우연히 없어서 안 보이는 것은 결정이 아니다.
```

GLOBAL seed 14개 중 3개 visible, **11개 explicit HIDDEN**.

---

## 4. 완료 게이트

| 게이트 | 내용 |
|---|---|
| **G1** | `resolved_set(BR) == {PSY, FARROWING_RATE, NPD}` |
| **G2** | `len(resolve_display_kpis(BR)) == 3` |
| **G3** | `headline_kpi(BR) == "PSY"` |
| **G4** | GLOBAL 에 KPI 가 추가돼도 BR visible set 이 **조용히** 늘지 않는다 |

### G4 구현 방식 (판단 근거)

G4 를 "GLOBAL 14→15 여도 BR 은 그대로" 로 **문자 그대로** 만족시키려면 리졸버에
COUNTRY scope default-deny 를 넣어야 한다. 그건 GLOBAL→COUNTRY 상속이라는 핵심 설계를
뒤집고 아직 시드하지 않은 US·KR 화면을 전부 비우므로 채택하지 않았다.

대신 **coverage 게이트**로 구현한다.

```
모든 GLOBAL visible KPI 는 BR 에 명시적 결정(visible 또는 HIDDEN)이 있어야 한다.
```

GLOBAL 에 KPI 를 추가하고 BR 결정을 빠뜨리면 이 테스트가 실패한다. 즉 **조용한 증가가
불가능해지고, 국가별 결정을 강제**한다. G4 의 의도("A 를 고른 진짜 이유를 고정")는 이쪽이
더 정확히 지킨다 — 사고를 막는 게 아니라 결정을 강제하는 것이기 때문이다.

---

## 4-1. D-10 결정 (2026-08-21) — GLOBAL 의 의미 재정의

`metrics` 맵 노출로 프론트가 그릴 수 있는 KPI 가 늘자, GLOBAL seed 가 14개를 전부
visible 로 둔 것이 **결정한 적 없는 지표를 11개국에 자동 노출**하는 경로임이 드러났다.
지금까지 4장만 보인 건 정책이 아니라 **프론트 구현 한계**였다.

| 결정 | 내용 |
|---|---|
| **D-10-1 (A)** | GLOBAL = 미결정 국가의 **최소 안전값** 3개(`PSY`·`NPD`·`FARROWING_RATE`). 나머지 11개 HIDDEN. 확대는 COUNTRY 명시 승인으로만 |
| **D-10-2 (B)** | BR 은 현행 3개 유지. 7개 확대는 UAT 완료 + 현지명 확정 후 별도 결정 |
| **D-10-3 (C)** | 비타겟 6개국(**PH·MX·DE·ES·DK·NL**) = `UNKNOWN / PENDING CLASSIFICATION`. 농장 성격(CUSTOMER/PILOT/HARVEST/TEST/INTERNAL/UNKNOWN) 확인 전까지 제품 타겟 승격·노출 확대 금지 |
| **D-10-4 (A)** | KR 도 별도 국가 정책 없이 GLOBAL 적용. 대표 검토용 전체 지표는 **국가 정책이 아니라 Admin KPI Preview** 로 분리(정책이 QA 도구 역할을 겸하면 "왜 KR만 14개냐" 예외가 생긴다) |

### 운영 영향 — "화면 변화 0" 이 아니다

`SOW_TURNOVER` 는 GLOBAL SECONDARY 였으므로 축소 시 **카드가 4장 → 3장이 된다.**
정확한 표현은 **"결정 없는 노출 확대 0"** 이다.

### GLOBAL visible 3개의 의미 범위

"카드를 표시할 수 있다"까지만이다. **"3개는 모든 나라에서 현지 기준까지 검증됐다"는
뜻이 아니다.** 축은 계속 분리된다.

```
Presentation policy   카드 표시 여부
Definition/Evidence   정의 호환성 · 근거 승인
Benchmark policy      국가 benchmark 사용 가능 여부 · severity 산출 가능 여부
Entitlement           FCR 등 유료/제한 기능 노출 여부
```

미국에서 PSY 카드를 표시하더라도, 미국 benchmark 가 승인되지 않았다면 미국 기준인 것처럼
severity·비교문구를 만들어서는 안 된다.

### 회귀 잠금

`tests/integration/test_global_visible_minimum.py` — **프론트 capability 증가 ≠ 제품
노출 증가**. 새 KPI 를 시스템에 추가해도 미결정 국가의 visible 카드 수가 늘지 않는다.

## 5. 변경 이력

| 버전 | 날짜 | 내용 |
|---|---|---|
| v0.4 | 2026-08-21 | D-10 확정 — GLOBAL 을 최소 안전값 3개로 재정의 · BR 3개 유지 · 비타겟 6개국 UNKNOWN · KR 은 GLOBAL 적용 + Admin Preview 분리. `BORN_ALIVE`·`PWMR`·`STILLBORN_RATE` 의 페이로드 제약 해소(남은 건 현지명) |
| v0.3 | 2026-08-20 | Pilot v1 visible subset(3) 신설 · full target(7) 유지 · `SOW_TURNOVER` explicit HIDDEN(근거 부재·현지명 UNVERIFIED) · seed 원칙 OPTION A · G1~G4 |
| v0.2 | — | full target 7개 확정 · 현지 명칭 3개 확정 |
