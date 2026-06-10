# PigOS Screen & Menu Specification

> Updated: 2026-06-10  
> Reference: PigPlan production logic + PigOS current dev state  
> Stack: Next.js 15 + TypeScript + TanStack Query + Tailwind

---

## Table of Contents
1. [Menu Structure](#menu-structure)
2. [Terminology — KR · EN · Regional](#terminology)
3. [Sow Breeding Cycle](#sow-breeding-cycle)
4. [Screen Specs](#screen-specs)
5. [Sow Status Definitions](#sow-status-definitions)
6. [Gap & Priority](#gap--priority)

---

## Menu Structure

```
PigOS
├── Dashboard              /dashboard
├── Sows                   /sows
├── Boars                  /boars
├── Events                 /record
├── Grow-Finish            /grow-finish
├── Reports
│   ├── Reproduction       /reports/reproduction
│   ├── Grow-Finish        /reports/grow-finish
│   └── KPI                /reports/kpi
├── Alerts / Tasks         /alerts
└── Settings
    ├── Farm               /settings/farm
    ├── Benchmarks         /settings/benchmarks
    └── Users              /settings/users
```

> **네이밍 근거**
> - "Sows" / "Boars" — 전 세계 양돈업계 표준. Pig Champ, Topigs Norsvin, ANIPIG 모두 동일
> - "Events" — 교배/분만/이유 입력을 하나로 묶는 글로벌 표준 용어 (Precision Livestock Farming 컨텍스트)
> - "Grow-Finish" — 미국 표준. EU는 "Finishing"이라고도 하지만 Grow-Finish가 더 넓게 통용
> - "Alerts / Tasks" — 관리현황. "To-do" 또는 "Overdue Events" 라고도 불림

---

## Terminology

한국어(PigPlan 기준) ↔ 글로벌 표준 영문 용어 대조표.  
**화면 표기는 EN 컬럼 기준으로 통일**

### 모돈 번식 관련
| 한국어 (PigPlan) | 영문 표준 | 지역별 차이 |
|-----------------|----------|------------|
| 모돈 | Sow | — |
| 후보돈 | Gilt | — |
| 웅돈 | Boar | — |
| 교배 | Mating / Service | EU: "Service", US: "Mating" or "Breeding" |
| 임신 | Gestation / Pregnant | — |
| 분만 | Farrowing | 전세계 동일 |
| 이유 | Weaning | — |
| 포유 | Lactation | — |
| 공태 | Open | "Non-pregnant", "Empty" 라고도 함 |
| 임신사고 | Return to Service (RTS) | Abort, Repeat Breeder 포함 개념 |
| 산차 | Parity | — |
| 재귀일 (WSI) | Weaning-to-Service Interval (WSI) | 전 세계 동일 약어 |
| 비생산일 | Non-Productive Days (NPD) | 전 세계 동일 약어 |
| 총산 | Total Born (TB) | — |
| 생존산 | Born Alive (BA) | — |
| 사산 | Stillborn (SB) | — |
| 미라 | Mummified (MUM) | — |
| 이유두수 | Weaned per Litter (WPL) | — |
| 이유일령 | Weaning Age / Days to Weaning | — |
| 이유전폐사율 | Pre-weaning Mortality Rate (PWMR) | — |
| 양자 / 포유이동 | Cross-fostering | 전 세계 동일 |

### 비육 관련
| 한국어 | 영문 표준 | 지역별 차이 |
|--------|----------|------------|
| 비육 | Grow-Finish | EU: "Finishing" |
| 자돈 (이유 후) | Nursery / Weaner | US: Nursery, EU: Weaner |
| 육성돈 | Grower | — |
| 비육돈 | Finisher | — |
| 일당증체량 | Average Daily Gain (ADG) | 전 세계 동일 약어 |
| 사료요율 | Feed Conversion Ratio (FCR) | 전 세계 동일 약어 |
| 출하 | Shipment / Slaughter | — |

### KPI 약어 (화면에 그대로 표기)
| 약어 | Full Name | 기준 |
|------|-----------|------|
| PSY | Pigs per Sow per Year | 글로벌 표준 |
| NPD | Non-Productive Days | 글로벌 표준 |
| FCR | Feed Conversion Ratio | 글로벌 표준 |
| WSI | Weaning-to-Service Interval | 글로벌 표준 |
| PWMR | Pre-weaning Mortality Rate | 글로벌 표준 |
| ADG | Average Daily Gain | 글로벌 표준 |
| TB / BA / SB | Total Born / Born Alive / Stillborn | 글로벌 표준 |

> ⚠️ **절대 사용 금지 표현**
> - `건유(Dry)` — 낙농(유우) 전용 용어. 돼지에 사용 불가.
> - `공태를 ACTIVE로 매핑` — ACTIVE는 상태 코드 아님. 아래 상태 정의 참고.

---

## Sow Breeding Cycle

```
Gilt (후보돈)
    │
    ▼  First Mating
[OPEN] ◄─── Weaning ◄─── [LACTATING] ◄─── Farrowing ◄───────────┐
   │                                                               │
   ├── Mating ──────────► [PREGNANT] ──────────────────────────── ┘
   │                          │
   │                          └── Return to Service (RTS) ──► [ACCIDENT]
   │                                                              │
   └──────────────────── Re-mating ◄────────────────────────────── ┘
   │
   ▼
[CULLED] ← 모든 상태에서 도태/폐사 가능
```

### Cycle Reference Values (Farm Config)
| Item | Code | Default | Used For |
|------|------|---------|----------|
| Avg. Gestation Length | 140002 | **114 days** | Farrowing due date |
| Avg. Lactation Length | 140003 | **21 days** | Weaning due date |
| Avg. WSI | 140008 | **7 days** | Next mating due date |
| Gilt First Mating Age | 140007 | **240 days** | Late mating alert |
| Target Slaughter Age | 140005 | **180 days** | Grow-finish due date |

---

## Screen Specs

---

### 1. Dashboard `/dashboard`

#### KPI Cards
| KPI | Display | Alert Threshold |
|-----|---------|----------------|
| PSY | 1 decimal | < 20 → warning |
| NPD | integer (days) | > 14 days → warning |
| Farrowing Rate | % | — |
| Sow Inventory | head (by status) | — |

#### PSY Grade System
| Grade | PSY Range | Color |
|-------|-----------|-------|
| Excellence | ≥ 28 | Green |
| Advanced | 24 – 27.9 | Blue |
| Stable | 20 – 23.9 | Yellow |
| Developing | < 20 | Red |

#### Widgets
- This week: Matings / Farrowings / Weanings
- Overdue sows count → link to `/alerts`
- Upcoming events (next 3 days)

---

### 2. Sows `/sows`

#### List
- Status filter tabs: `All` / `Gilt` / `Open` / `Pregnant` / `Lactating` / `Accident` / `Culled`
- Columns: Ear Tag, Breed, Entry Date, Status, Parity, Last Event, Actions
- Search by ear tag

#### Register Modal
| Field | Type | Required | Note |
|-------|------|----------|------|
| Ear Tag | text | ✅ | Duplicate check → server 409 |
| Entry Date | date | ✅ | |
| Entry Type | select | ✅ | Gilt / Purchase / Transfer / Own-bred |
| Breed | select | — | |
| Parity | number | — | For transferred sows |
| Date of Birth | date | — | For age calculation |

#### Edit Modal ← **Not implemented — highest priority**
- Ear tag, breed, entry type, date of birth

#### Cull / Death Modal
| Field | Type |
|-------|------|
| Date | date |
| Type | select: Cull / Death / Transfer / Sale |
| Reason | select: Reproductive failure / Age / Disease / Injury / Other |

#### Sow Detail `/sows/[id]`
- Info card
- **Breeding history timeline**: Mating → Farrowing → Weaning cycle
- Parity table: Parity no. / Mating date / Farrowing date / TB / BA / Weaned / Weaning age
- Current status + next expected event

---

### 3. Boars `/boars` ✅ Done

- Register modal: Ear tag / Breed / Stud farm / Entry date / Entry type / Semen quality
- Edit modal
- Status change: Cull / Death / Transfer

---

### 4. Events `/record`

**Flow**: Search sow → Select → Fill event form → Save → "Next sow" (continuous entry)

URL query `?tab=` for direct tab access.

#### Tab: Mating `?tab=mating`
| Field | Note |
|-------|------|
| Mating Date | Must be after last weaning/accident date |
| Method 1/2/3 | AI / Natural / combo — sequential input (2 requires 1) |
| Boar 1/2/3 | Sequential (2 requires 1) |
| Service No. | Auto-calculated (1st / 2nd / 3rd service) |

**Validation**:
- Eligible status: Gilt / Open / Accident only
- Date must be after last recorded event

#### Tab: Farrowing `?tab=farrowing`
| Field | Limit | Note |
|-------|-------|------|
| Farrowing Date | — | ~114 days after mating |
| Total Born (TB) | max **35** | |
| Born Alive (BA) | ≤ TB | |
| Stillborn (SB) | max **25** | |
| Mummified (MUM) | max **25** | |
| Avg. Birth Weight | max **3.0 kg** | |
| Farrowing Ease | — | Normal / Difficult / Very difficult / C-section |
| Cross-fostering | — | Links to piglet transfer |

**Validation**:
- TB ≤ 35, SB/MUM each ≤ 25
- Born Alive = Male + Female (if entered separately)

#### Tab: Weaning `?tab=weaning`
| Field | Note |
|-------|------|
| Weaning Date | After farrowing date |
| Weaned (head) | = Nursing head − (Deaths + Transfers out − Transfers in) |
| Total Weaning Weight (kg) | |
| Avg. Weaning Age (days) | Auto-calculated |

#### Tab: Return to Service (RTS) `?tab=accident`
| Field | Note |
|-------|------|
| Date | |
| Type | Repeat / Abort / Pseudo-pregnancy / Other |
| Note | |

#### Tab: Culling / Death `?tab=culling`
| Field | Note |
|-------|------|
| Date | |
| Type | Cull / Death / Transfer / Sale |
| Reason | |

**Cull recommendation triggers**:
- ≥ 3 consecutive RTS events
- Parity > 7 AND last litter weaned < 9 piglets
- Gilt age > 300 days with no mating

#### Tab: Cross-fostering `?tab=piglet-transfer`
- From sow / To sow
- No. of piglets (max **25** per transfer)
- Date

#### Tab: Piglet Group `?tab=piglet-group`
- Auto-created on weaning, or manual
- Group name, entry age, location

#### Tab: Grow-Finish `?tab=grow-finish`
- Group select or new group
- Head count, entry age
- Shipment: head count, weight, destination

---

### 5. Grow-Finish `/grow-finish`

#### Group List
- Columns: Group ID, Entry Date, Current Age (days), Head Count, Expected Ship Date, Status
- Status filter: Active / Completed

#### Age Segments
| Segment | Age Range |
|---------|-----------|
| Nursery | ≤ 70 days |
| Grower | 71 – 105 days |
| Early Finisher | 106 – 140 days |
| Late Finisher | > 140 days |

#### Group Detail
- Head count change log (Entry / Death / Transfer / Shipment)
- ADG vs. target chart
- Expected ship date: `Entry date + (Target slaughter age − Entry age)`

#### Shipment `/grow-finish/shipment`
- Groups approaching target age
- Record shipment: head count, weight, destination, price

---

### 6. Reports

#### Reproduction `/reports/reproduction`

Period selector: Month / Quarter / Year

| KPI | Formula |
|-----|---------|
| Services | Count of mating events in period |
| Farrowings | Count of farrowing events in period |
| Farrowing Rate | Farrowings / Services × 100 |
| Avg. Total Born | Mean TB of farrowings in period |
| Total Weaned | Sum of weaned piglets in period |
| Avg. Weaning Age | Mean days to weaning |
| PSY | Annual weaned / avg. sow inventory |
| NPD | Avg. days from weaning to next service |
| PWMR (Method A) | Deaths / (Weaned + Deaths) × 100 |
| PWMR (Method B) | (Avg. TB − Avg. Weaned) / Avg. TB × 100 |

> ⚠️ PWMR Method A vs B can differ by 3–5%p. **Always label which method is shown.**

#### Grow-Finish `/reports/grow-finish`
| KPI | Formula |
|-----|---------|
| ADG | (Ship weight − Entry weight) / Days on feed |
| FCR | Feed consumed / Weight gain |
| Mortality Rate | Deaths / Entry head × 100 |
| Avg. Days to Market | |

#### KPI Trends `/reports/kpi`
- PSY monthly trend chart
- NPD trend chart
- Farrowing Rate trend
- Benchmark reference lines (from `/settings/benchmarks`)

---

### 7. Alerts / Tasks `/alerts`

#### Overdue Sow Types (6 categories)
| Type | Trigger | Recommended Action |
|------|---------|-------------------|
| Gilt — first estrus check | No estrus recorded after entry | Check heat |
| Gilt — overdue for first mating | Age > target first mating age (240d) | Mate or cull |
| Breeding — farrowing overdue | No farrowing after gestation length (114d) | Pregnancy check |
| Farrowing — weaning overdue | No weaning after lactation length (21d) | Wean |
| Weaning — re-service overdue | No mating after WSI (7d) | Mate |
| RTS — re-service overdue | No re-mating after return to service | Mate or cull |

#### Cull Recommendations
| Criterion | Condition |
|-----------|-----------|
| Repeat RTS | ≥ 3 consecutive returns to service |
| Aged low performer | Parity > 7 AND last weaned < 9 piglets |
| Overdue gilt | Age > 300 days, never mated |

Each row: action button → `/record?tab=mating&sowId=xxx`

---

### 8. Settings

#### Farm Settings `/settings/farm`
| Item | Default | Description |
|------|---------|-------------|
| Avg. Gestation Length | 114 days | Farrowing due date calculation |
| Avg. Lactation Length | 21 days | Weaning due date calculation |
| Avg. WSI | 7 days | Re-service due date calculation |
| Gilt First Mating Age | 240 days | Alert trigger |
| Target Slaughter Age | 180 days | Grow-finish due date |
| Target Slaughter Weight | kg | |

#### Benchmarks `/settings/benchmarks`
- Target PSY
- Target NPD
- Target Farrowing Rate
- Target Weaned per Litter
- *(Country-specific defaults — future)*

#### Users `/settings/users`
- Invite / role management within farm

---

## Sow Status Definitions

| Status Code | Display (EN) | Display (KR) | Description |
|-------------|-------------|-------------|-------------|
| `GILT` | Gilt | 후보돈 | Entered farm, not yet mated |
| `OPEN` | Open | 공태 | Post-weaning, awaiting mating |
| `PREGNANT` | Pregnant | 임신 | Post-mating, pre-farrowing |
| `LACTATING` | Lactating | 포유 | Post-farrowing, nursing |
| `ACCIDENT` | RTS / Accident | 사고 | Post-RTS, awaiting re-mating |
| `CULLED` | Culled | 도태 | Removed from herd |

---

## Gap & Priority

### P0 — Fix Now
- [ ] **Sow Edit UI** — PATCH API exists, no UI
- [ ] **Status terminology** — fix ACTIVE→Open mapping, remove "Dry" (dairy term)

### P1 — Next Sprint
- [ ] **Sow detail page** `/sows/[id]` — breeding history timeline
- [ ] **Alerts screen** `/alerts` — 6 overdue types + cull recommendations
- [ ] **Reproduction report** `/reports/reproduction`

### P2 — Upcoming
- [ ] Front-end validation (date overlap, head count limits with inline messages)
- [ ] Replace emoji icons in QuickInputDrawer with Lucide/SVG
- [ ] Mobile layout for `/record`
- [ ] Country-specific units & benchmarks (linked to onboarding country select)

### P3 — Roadmap
- [ ] PWMR method toggle (A vs B) in reports
- [ ] Photo / voice input
- [ ] Excel bulk import (2,000 rows)
- [ ] PSY grade certificate export

---

## Screen → URL → Status Transition Map

| Event | Entry Point | Status Change |
|-------|------------|--------------|
| Mating | `/record?tab=mating` | Gilt / Open / Accident → **Pregnant** |
| Farrowing | `/record?tab=farrowing` | Pregnant → **Lactating** |
| Weaning | `/record?tab=weaning` | Lactating → **Open** |
| Return to Service | `/record?tab=accident` | Pregnant → **Accident** |
| Cull / Death | `/record?tab=culling` | Any → **Culled** |
| Sow detail | `/sows/[id]` | No change (read) |
| Alerts | `/alerts` | No change (read + navigate) |
