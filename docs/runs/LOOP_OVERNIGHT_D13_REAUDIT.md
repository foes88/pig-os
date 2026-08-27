# 밤샘 런 — D-13 재실사 (A ∩ B ∩ B′ 열거)

```
Mode      : READ-ONLY 감사. 코드·seed·마이그레이션·설정 변경 0
Baseline  : 2fedb9c   ★ 이 해시에서 벗어나면 즉시 STOP
Machine   : bjh 전용
산출물    : docs/kpi/CANONICAL_FORMULA_SPEC_REAUDIT.md 1개 (신규)
Git       : 로컬 커밋만. push 금지. 배포 금지
프로덕션  : SELECT 만. 쓰기·설정변경·flag 토글 전면 금지
```

---

## 0. 이 런이 존재하는 이유 — 먼저 읽어라

1차 D-13 은 `CONFIRMED 7` 을 냈고 **그중 5건이 무효**였다. 하루에 판정이 **다섯 번**
뒤집혔다. 그러니 이 런의 목표는 "빨리 끝내기" 가 아니라 **뒤집히지 않는 결과를 내는 것**이다.

### 오늘 뒤집힌 다섯 번과 원인

| # | 오류 | 원인 |
|---|---|---|
| 1 | "11룰이 하드코딩 상수로 색을 낸다" | resolver 체인만 보고 **호출자 미확인** |
| 2 | "37룰은 임계 없음" | **핸들러 본문만 grep** — 헬퍼(`_common.resolve`)를 관통 안 함 |
| 3 | "실고객 노출 사실상 0" | **모집단(`data_origin`) 미분리** |
| 4 | "US 는 승인 벤치마크 없음" | `country_kpi_policy` 부재에서 `default_metric_values` 부재를 **추론** |
| 5 | "단일 경로 7건 / NPD CLEAN" | 산식→호출자 **한 방향만** 추적 |

```
공통 실패 모드
  ① 호출 그래프를 한 단계만 보고 판정한다
  ② 집계 전에 모집단을 나누지 않는다
  ③ "X 가 없다" 를 다른 테이블·다른 계층의 부재에서 추론한다
```

**이 세 가지를 하지 않는 것이 이 런의 전부다.**

---

## 1. 하드 규칙 — 위반 시 즉시 STOP + 리포트

```
✗ push · 배포 · 프로덕션 쓰기 · 설정 변경 · USE_GOVERNANCE_BENCHMARKS 토글
✗ 코드 · 테스트 · seed · 마이그레이션 수정  (재실사는 read-only 다)
✗ 법무 빈칸 · 미확보 수치 날조
✗ 막히거나 애매한데 "아마" 로 넘어가기
✓ 로컬 커밋만 (1변경 = 1커밋, trailer 포함)
✓ 막히면 멈추고 리포트. 부분 결과라도 남긴다
```

**baseline 이탈 검사** — 각 작업 단위 시작 전:
```bash
git rev-parse HEAD    # 2fedb9c 가 아니면 STOP_REASON: BASELINE_DRIFT
```

---

## 2. 판정 기준 — 이미 고정됨. 완화 금지

`CANONICAL_FORMULA_SPEC.md` §3 신설 기준:

```
셋을 동시에 충족해야만 CONFIRMED
  ① 실제 코드 라인 인용 (파일:행)
  ② 해당 산식의 테스트 통과
  ③ 실데이터 1건 수기 검산 일치

하나라도 빠지면 UNVERIFIED. 문서 대조만으로 CONFIRMED 금지.
```

★ **③ 수기 검산이 이번 런의 핵심이다.** ①②만으로는 `/kpi/trend` 같은
"코드도 맞고 테스트도 통과하는데 필드에 다른 지표가 담긴" 경우를 못 잡는다.
실데이터를 직접 넣고 손으로 계산해 값이 맞는지 본다.

★ 현재 상태: `CONFIRMED 0 · REVOKED 5 · PENDING_RECHECK 2 · AMBIGUOUS 2`.
**"반증 안 됐으니 유효" 는 금지다** — 입증 책임은 CONFIRMED 쪽에 있다.

---

## 3. 열거 — 탐색이 아니다

끝나고도 "전 경로를 안 훑었으므로 더 있을 수 있다" 가 남으면 **부분 탐색 4회차**다.

### A축 — 산식 함수 → 호출자 역추적

각 산식 함수에서 **호출자를 끝까지** 따라간다. 헬퍼를 관통한다(실패 모드 ①·②).

```
대상: calculate_psy · calculate_npd · _cohort_farrowing_rate · build_herd_kpis ·
      _avg_active_inventory · npd_repo.* · get_trend · report_service.* ·
      insight_service.* · jobs/kpi.py · scorecard_service.*
```

각 호출자에 대해 `path_reachability` 를 기록한다: `LIVE | DEAD | TEST_ONLY | UNKNOWN`
+ `route → service → function` 근거. 근거 없으면 `UNKNOWN` (승격 금지).

### B축 — 응답 필드명 → 실제 담기는 산식

**반대 방향.** `api/app/schemas/*.py` 의 모든 KPI 필드를 열거하고, 각각에 **실제로
어떤 산식의 결과가 들어가는지** 역추적한다.

```
왜 필요한가: /kpi/trend 는 필드명이 npd 인데 값은 WEI 였다.
             A축(산식→호출자)만으로는 이걸 못 잡는다. 실제로 못 잡았다.
```

### B′축 — 모바일 DTO 매핑 (신규)

```
백엔드 필드 → Android DTO 필드 → 화면 표시값
백엔드 필드 → iOS   모델 필드 → 화면 표시값
```

**핵심 질문: 모바일이 하드코딩하는 것이 "라벨" 인가 "산식" 인가.**
라벨만이면 재실사 대상이 아니다. 자체 계산·재매핑이면 `/kpi/trend` 와 똑같은 구조의
오염이 Android·iOS 에 **각각** 존재할 수 있다.

이미 단서가 하나 있다 — **iOS 는 알림 severity 를 다시 매칭해 색을 낸다**(Codex C-4).
서버 판정을 그대로 안 쓰는 계층이 최소 하나 있고, **값에도 손대는지는 미확인**이다.

```
Android  C:\dev\pigos-android   read-only
iOS      C:\dev\pigos-ios       read-only
★ 모바일 저장소는 수정 금지. commit hash 를 기록한다(재현성)
```

### 완료 기준

```
A ∩ B ∩ B′ 교차 대조가 끝나고, 세 축 중 어느 축에서도 미추적 경로가 0 일 때.
"더 있을 수 있다" 를 쓸 수 없는 상태가 완료다.
```

---

## 4. 모집단 규율 (실패 모드 ②)

프로덕션 수치를 낼 때 **`data_origin` 으로 반드시 나눈다.**

```
farms.data_origin = 'pigplan_migration'  →  INTERNAL_REFERENCE
farms.data_origin = 'native_signup'      →  LIVE_CUSTOMER

합산 통계는 그 사실을 명시하지 않으면 사용 금지.
운영 판정(인시던트 등급·고객 영향)은 LIVE_CUSTOMER 로만.
표본이 작으면 "산출 불가" 로 적는다 — "영향 없음" 이 아니다.
```

★ 아키텍처 `§2-1-A`. 오늘 이걸 안 해서 참조 데이터 통계를 인시던트로 보고했다.

---

## 5. 추론 금지 (실패 모드 ③)

```
"country_kpi_policy 에 US 행이 없다"  ≠  "default_metric_values 에도 없다"
                                          ← 다른 테이블이다. 조회해라
"핸들러 본문에 안 보인다"              ≠  "임계값을 안 쓴다"
                                          ← 헬퍼를 관통해라
"반증되지 않았다"                      ≠  "CONFIRMED"
                                          ← 입증 책임은 이쪽에 있다
```

**"X 가 없다" 를 주장하려면 X 를 담을 수 있는 표면을 전부 열거하고 각각을 확인한다.**

---

## 6. 산출물 구조

`docs/kpi/CANONICAL_FORMULA_SPEC_REAUDIT.md`

```
0.  Status (baseline / machine / 3 repo commit / tests / 실행일)
1.  A축 — 산식 함수 → 호출자 전수표 (reachability 근거 포함)
2.  B축 — 응답 필드 → 실제 산식 전수표
3.  B′축 — 모바일 DTO 매핑 전수표 (라벨 vs 산식 판정)
4.  교차 대조 결과 — A ∩ B ∩ B′ 에서 어긋나는 지점
5.  KPI 별 판정 (기준 ①②③ 충족 여부를 각각 표기)
6.  신규 발견 divergence / 오염
7.  ③ 수기 검산 기록 (KPI 별 실데이터 1건 · 손계산 · 일치 여부)
8.  미추적으로 남은 것 — 왜 못 했는지. **비어 있어야 완료다**
9.  Explicit Non-Changes
```

각 KPI 판정은 반드시 이 형태:

```
PSY   ① kpi_service.py:60-121  ② test_xxx::test_yyy PASSED
      ③ farm <id> 2026-07 → 분자 1,234 / 분모 56.7 = 21.76, API 21.76  일치
      → CONFIRMED
```

②나 ③이 비면 `UNVERIFIED` 다. **비어 있는데 CONFIRMED 로 쓰면 이 런은 실패다.**

---

## 7. 진행 순서

```
1) baseline 확인 (2fedb9c)
2) B축 먼저 — 응답 필드 전수 열거 (가장 싸고, /kpi/trend 를 잡은 방향이다)
3) A축 — B축에서 나온 산식들의 호출자 역추적
4) B′축 — 모바일 DTO 매핑
5) 교차 대조 → 어긋나는 지점 목록
6) 각 KPI 에 ①②③ 적용. ③은 프로덕션 SELECT + 손계산
7) 산출물 작성 → 로컬 커밋 (push 금지)
```

**2)를 먼저 하는 이유**: A축부터 가면 오늘과 같은 결과가 나온다. 오염을 실제로 잡은 것은
B축이었다.

---

## 8. STOP 조건

```
STOP_REASON: BASELINE_DRIFT          HEAD ≠ 2fedb9c
STOP_REASON: WRITE_ATTEMPT_BLOCKED   코드·설정·프로덕션 쓰기가 필요해진 경우
STOP_REASON: SCOPE_AMBIGUOUS         감사 범위 판단이 필요한 경우(사람 결정)
STOP_REASON: DATA_INSUFFICIENT       ③ 수기 검산에 쓸 실데이터가 없는 KPI
STOP_REASON: BUDGET                  시간·토큰 소진
```

STOP 시에도 **거기까지의 전수표는 남긴다.** 부분 결과가 없는 STOP 은 다음 런이
처음부터 다시 하게 만든다.

---

## 9. 이 런에서 하지 않을 것

```
✗ divergence 제거 (코드 정렬)      — 재실사 결과가 나온 뒤, 결재 후
✗ _avg_active_inventory 수정        — PSY 가 REVOKED 라 복사할 원본이 없다
✗ /kpi/trend 원인 수정              — 노출은 이미 차단됨(5abb8a4). 원인은 재실사 후
✗ D-19 origin 승격                  — 결재 사안
✗ 사산 P0-2 결재문 갱신             — 재실사 결과가 적용범위 조항이 된다
✗ 모바일 코드 수정                  — read-only
```

---

## 10. 참고 문서

```
docs/kpi/CANONICAL_FORMULA_SPEC.md          현 상태(CONFIRMED 0) · 판정기준 · A∩B∩B′
docs/kpi/D19_THRESHOLD_SOURCE_AUDIT.md      threshold source (오진 3회 기록)
docs/kpi/D20_DIVERGENCE_IMPACT.md           모집단 분리 사례 + 반증
handoff/CODEX_RESULT_2026-08-27.md          독립검증 — 반증 3 · 과장 6
docs/MOBILE_PARITY.md                       모바일 갭 (B′ 축 입력)
docs/runs/RUN_PROMPT_D13_canonical_formula_audit.md   1차 실행 스펙 v1.4
```
