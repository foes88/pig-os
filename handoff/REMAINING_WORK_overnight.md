# PigOS 남은 작업 정리 (밤샘 프롬프트 생성용)

> 작성 2026-06-25. 각 항목은 그대로 프롬프트로 만들 수 있게 목표/범위/인수조건/가드레일/선행상태 포함.
> 공통 절대규칙(모든 프롬프트에 넣을 것): 운영 DB·배포·스토리지 금지 / git push 금지 / 수치 임의생성 금지 /
> 테스트 안 한 항목 PASS 금지 / 확신 안 서면 멈추고 보고 / dev 전용.

## 현재 상태 (선행)
- dev migration head = **`f2b4d6e8a0c1`** (작업 A·B·C·US·operational_defaults 적용)
- 전체 테스트 **587 passed**. 운영 미배포(전부 additive, `USE_GOVERNANCE_BENCHMARKS=False`=현행 동작).
- 완료: 3-table governance(kpi_definitions16/source_observations/benchmarks) + KR verified7·normalized1·provisional6·missing1 + US verified1·normalized1·missing1 + operational_defaults 29(코드 임계 1:1 이전) + benchmark resolver(read) + 읽기 admin API.
- 핵심 문서: `handoff/KPI_GOVERNANCE_v3.1.md`(§10 v3.2) / `OPEN_DECISIONS_for_user.md` / `operational_default_inventory.md`.

---

## TRACK 1 — A-하이브리드 연결 마무리 (최우선, 이어서) ★

> 기준: `handoff/KPI_GOVERNANCE_v3.1.md` + "Rule Engine ↔ 3-table 연결 (A-하이브리드 확정본)" 프롬프트.
> 원칙: **발화=threshold(rule_configs→operational_defaults) / 맥락=governance verified 평균. 둘 안 섞고 trace 각각.**
> [✅2.0 인벤토리][✅2.1 레지스트리 시드29][✅2.2 1:1 발화동일성] 까지 끝. 아래 3~6 남음.

### T1-3. Threshold Resolver (발화 권위)
- 목표: 룰이 인라인 임계 대신 **rule_configs → operational_defaults** 에서 임계를 읽게 한다.
- 작업: `_common.resolve()` + `reproduction.py _thresholds/_cfg_default` + (base 특수형은 ㉮로 유지)을 operational_defaults 조회로 교체. **flag ON일 때만** 새 경로, OFF면 현행.
- direction은 governance KPI면 `kpi_definitions.direction` 우선(override 금지), 비-governance KPI(ADG·BIRTH_WEIGHT 등)는 operational_defaults.direction.
- value_scale: threshold↔farm_value 일치 검사(불일치→발화금지 insufficient).
- 인수조건: **1:1 발화 동일성**(flag ON 결과 == flag OFF 결과)을 fixture로 증명. operational_defaults가 코드값과 같으니 동작 불변이어야.
- 가드레일: operational_defaults는 threshold 전용. benchmark/평균으로 쓰지 말 것. 옛 default_metric_values 재사용 금지.

### T1-4. Benchmark Context Resolver (맥락 전용)
- 목표: 기존 `services/benchmark_service.py`를 §5 의미로 조정 — verified/normalized 평균은 **맥락 첨부**, provisional/missing은 맥락도 금지, value_scale mismatch는 **발화 막지 말고 맥락만 강등**.
- 작업: resolve_benchmark_context() 분리(현 resolve_benchmark는 can_fire 프레이밍 → 맥락 프레이밍으로). US stillbirth normalized 첨부 가능(§8.1 조건), PWMFY→PSY 맥락도 금지(§8.2).
- 인수조건: provisional 평균이 사용자 노출 0건 / global_fallback 맥락은 `is_global_fallback=true` trace.

### T1-5. 엔진 배선 + insight trace
- 목표: Rule Engine이 두 resolver를 호출(threshold로 발화, context로 평균 첨부). **`USE_GOVERNANCE_BENCHMARKS` 기본 OFF**(현행) → diff 합격 후 전환 논의.
- trace 필수(§7): kpi_code·farm_value·threshold_source·warning/critical·direction·value_scale·severity·benchmark_source·benchmark_id·benchmark_status·comparison_status·source_obs_id·obs_group_id·is_global_fallback·insufficient_reason.
- 인수조건: 생성 insight에 trace 남음 / flag=false면 전체 롤백(현행 동일).

### T1-6. baseline + before/after diff (§10 관문) ★검증 핵심
- 고정 fixture set(최소 KR·US·global_fallback 국가 포함) 생성·고정.
- before(현행) vs after(flag ON): `country×kpi` 발화적격수 / `country×rule_id×severity` insight수 / threshold 커버리지.
- 합격: **발화 수 ≈ 유지**(A는 임계 출처를 operational_defaults로 보존하므로). KR 급감하면 버그→멈춤·보고.
- 절대중단: provisional/missing/incompatible/unknown 평균이 사용자 발화에 쓰임 / 평균이 threshold처럼 발화에 쓰임 / value_scale mismatch인데 발화.
- 출력: diff 표 + operational_defaults 전체목록(값+출처) + US회귀 + KR27 역검증.

---

## TRACK 2 — 국가 데이터 확장 (사용자 자료/결정 필요)

### T2-1. EU/GB 적재 — **D-3 결정 선행**
- D-3: GB를 country 단위로 indoor/outdoor/평균 중 무엇? (잠정 GB_indoor)
- 자료: AHDB/InterPIG 2024(EU weaned 30.27 / GB indoor 28.0 / outdoor 24.6) — production_system 분리돼야 의미.
- 처리: D-3 전엔 provisional. 분모=상시모돈이라 KR/US와 comparison=compatible.

### T2-2. BR/VN/CN — **1차자료 확보 후만**
- BR(Agriness)·VN(WEPIG)·CN 1차 수치 미확보 → 시드 금지(위조0). 확보 시 정의·모집단·period 검증 후 verified/provisional.

### T2-3. TH/MX — global_fallback
- 1차자료 없음 → `benchmark_status='global_fallback'` + 명시 threshold 있을 때만 발화, `is_global_fallback=true` trace.

---

## TRACK 3 — 배포 + 운영

### T3-1. 운영 배포 (A·B·C·US·operational_defaults 묶음) — **사용자 확인 필요**
- 전부 additive·flag OFF라 동작 변화 0. 마이그레이션 6종(c5e7a9b1d3f0→f2b4d6e8a0c1) 운영 적용.
- 순서: 빌드 → alembic upgrade(빌드 후) → web/api/worker force-recreate → 3도메인 200 스모크.
- ⚠️ worker는 자체 이미지(`build worker` 별도). 운영 docker sudo. (handoff/VERIFICATION_HANDOFF_for_codex.md 배포메모)
- CLAUDE.md head 값 갱신.

---

## TRACK 4 — 잔여 폴리시 (비블로커, 이월)

- **챗 cause/action 코드 현지화**(~80코드×7어, raw snake_case 노출) — i18n 마감
- **M3/F4 PigPlan 패리티(LOW)** — M3 AI방식 슬롯 시퀀스 / F4 사인별 폐사 25상한
- **D-7 실행**: SOW_RESIDUAL/SALVAGE 원화 누수 → loss.py country='KR' 게이트(출시前 분리, 통화일반화 P2)
- **PeriodLockedError 409→423** 데드코드 정리

---

## 사용자 결정/자료 대기 (OPEN_DECISIONS_for_user.md 참조)
- 🔴 BR/VN 앵커마켓 1차자료 / D-3(GB) — 자료·결정
- 🟡 D-1(NPD 후보돈 포함) — KR/US verified와 무관, NPD 시드할 국가 생길 때
- DB: Supabase 무료 유지(auto-pause 방지됨), 가입 늘면 Pro

## 권장 밤샘 순서
1. **T1-3 → T1-4 → T1-5 → T1-6** (A-하이브리드 완성, flag OFF, diff 합격까지) ← 최우선
2. T4 폴리시(챗 현지화·D-7 게이트) — 독립적이라 병행 가능
3. T2/T3은 사용자 자료·확인 필요 → 대기
