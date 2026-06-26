# PigOS 데이터 정합성 — 검증 & 갭 보강 요청

## 읽을 것 (먼저)
- `handoff/pigplan-domain-integrity.md` — 모돈 데이터 꼬임 원인 + 도메인 불변식 + **§7 PigOS 현황 대비(✅된것/⚠️검증/🆕갭)**
- `handoff/pigplan-rules/README.md` + `pigplan_ai_rules_reference.md` — KR 룰셋(VALID_RANGES·DATA_QUALITY_GUARD·KPI_DRIVER_MAP 등 검증식 근거)

## 전제 (다시 만들지 말 것 — 이미 됨)
PigOS는 이미 성숙: `sows.id`(UUID)+`ear_tag`(farm 유니크), 이벤트 분리테이블(matings/farrowings/weanings/…), `breeding_cycles`(산차별, 활성1개 부분유니크), 두수 보존식 자동계산(`total_born=born_alive+stillborn+mummified`, ge=0), 오프라인 멱등성(client UUID→merge, conflict 로그), farm_id 스코프. **이 구조는 유지. 재설계 금지.**

## 목표
위 구조 위에서 **데이터 누수·꼬임이 구조적으로 불가능**하게 만든다. **꼬이면 망한다** — 모돈별·산차별·이벤트별로 절대 안 꼬여야 한다.

## ★ 최우선 — 무결성 4겹 코어 (`pigplan-domain-integrity.md` §8)
산발적 if 검증이 아니라 **불변식을 시스템이 강제**하도록 아래 4개를 명시적 구조로 둔다. 현재 코드에 있으면 검증·강화, 없으면 구현:
1. **상태머신(§8-1)**: 모돈은 항상 정확히 1상태, 전이는 이벤트로만. 불법 전이(분만 while ≠PREGNANT, 이유 while ≠LACTATING 등) = **입력 거부**. status는 이벤트에서 파생(저장값은 캐시).
2. **산차별 자돈 원장(§8-2)**: `(sow_id, parity)`마다 double-entry 원장. `born_alive+fostered_in = weaned+died+fostered_out+still_nursing`, 항상 balance. **양자=짝지은 2기입(원자적)**, 한쪽만 기록 금지. 음수·초과·미마감 = reject.
3. **이벤트 계약(§8-3)**: 모든 이벤트가 precondition→idempotency→occurred_at순 파생→invariant검증→atomic트랜잭션→append-only. **occurred_at(논리시각)으로 파생**, created_at(도착시각) 정렬 금지(오프라인 순서보존).
4. **정기 정합성 감사(§8-4)**: 저장 집계를 이벤트로그에서 재파생해 매일 대조, 드리프트 즉시 flag → 어드민 정합성 대시보드. (PigPlan은 꼬임을 몇 달 뒤 발견 — PigOS는 당일 탐지)

이 4겹이 "안 꼬인다"의 구조적 보장. 아래 ⚠️/🆕는 이 코어의 세부.

## 작업 (코드로 확인 후 보강)

### ⚠️ 검증 — 있는지 확인하고 없으면 추가
1. **ear_tag 재사용**: `UniqueConstraint(farm_id, ear_tag)`가 전체유니크면, 퇴출(exit_date) 모돈 번호를 새 모돈에 못 붙임. 현장은 도태 후 번호 재사용이 흔함 → **부분유니크(`WHERE exit_date IS NULL`)** 로 바꿀지 결정·구현.
2. **이벤트 간 불변식** (입력 validation 강화):
   - 날짜순서: `교배일 < 분만일(≈교배+114일) < 이유일(분만+포유기간)`, 미래일자 거부
   - 두수 흐름: `이유두수 ≤ 포유개시두수(실산 ± 양자)`, `포유중폐사 = 포유개시 − 이유 (≥0)`
   - 산차 연속성: 분만 시 parity +1, 역행/건너뜀 차단; `breeding_cycles`와 일관
3. **범위/극단값 가드**: 임신 110~120·포유 14~50·LSY≤2.66·PSY≤45·NPD≤200 → 입력거부 또는 경고. **국가별 정상범위는 `default_metric_values` scope로**(코드 하드코딩 금지).
4. **양자(cross-fostering)**: 포유 중 자돈 이동 시 두 모돈 산차의 두수 보존 처리(두수 꼬임 최대 지점).

### 🆕 갭 — 신규
5. **단위·로캘 정규화**(다국가): 저장은 정규형(kg·UTC·ISO·WOAH 질병코드) 단일, 표시만 국가별 변환. 입력 즉시 정규화.
6. **정정(correction) 의미론**: 과거 이벤트 수정 → 영향 산차/KPI 재계산 트리거 + as-of 재현(이벤트 리플레이). 수정 권한은 role 게이트.
7. **하드삭제 cascade 원자성**: 모돈 하드삭제 경로가 있으면 연관 이벤트 전부 한 트랜잭션(부분삭제 금지). 기본은 exit_date 소프트퇴출 유지.

## ★★ 모든 case를 연다 (`pigplan-domain-integrity.md` §9)
**happy-path만 짜면 현장 데이터 한 번 꼬이고 농가 이탈한다.** §9 엣지케이스 전수 카탈로그(10 카테고리: 교배·임신감정·분만·양자·이유·폐사도태·전입·산차·동기화·정정)의 **모든 row가 각각 정의된 동작 + 테스트**를 가져야 한다.
- 특히 **양자(cross-fostering, §9-D)**·**동기화 역순도착(§9-I)**·**마감산차 정정(§9-J)** 이 두수 꼬임 최대 지점 — 반드시 케이스별 테스트.
- "이 case는 안 일어남" 가정 **금지**. 현장은 다 일어난다. §9에 없는 케이스도 PigOS가 발굴해 채울 것.
- 산출물: **케이스 매트릭스**(case → 현재동작 있음/없음 → 처리정의 → 테스트) 전수 작성 후 미구현분 보강.

## 수용기준
- 검증식은 **server-side가 SSOT로 hard-block**(불변식 위반), client는 즉시경고. 오프라인 입력도 sync 시 server 재검증.
- §9 모든 케이스에 대응 테스트(unit/E2E) 존재. 두수 원장은 **property-based test**로 "어떤 이벤트 시퀀스에도 원장 balance" 검증 권장.
- hard-block: 두수 보존 위반·음수·산차역행·무효범위·날짜역순. warning: off-week 0두 등 비정상이지만 가능.
- 국가차이는 전부 scope 데이터(`default_metric_values`/`ComplianceProfile`), `if country==…` 하드코딩 금지.
- 기존 테넌트·이벤트 구조 회귀 없을 것. 변경은 테스트(E2E/unit) 동반.

## 먼저 할 일
1. §7의 ✅ 항목을 코드로 재확인(맞으면 패스), ⚠️ 4개를 **현재 enforce 여부** 코드로 점검.
2. 갭/미흡 목록 + 보강 설계(스키마·validator·마이그레이션) 제안 → 합의 후 구현.
3. 한 번에 다 하지 말고 ⚠️1~4 → 🆕5~7 순서.
