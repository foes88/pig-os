# TRACK 4 야간 스펙 (무인 판정용 인수조건) — 3개 게이트

> T1 동일 형식: 목표·작업·인수조건(머신 판정 가능)·가드레일. M3/F4는 통과기준 미정 → **제외**(본 문서 미포함).
> 공통 가드레일: dev 전용 / push·배포 금지 / 수치 임의생성 금지 / 테스트 안 한 항목 PASS 금지 /
>   확신 안 서면 STOP+로그 / Windows PowerShell / 게이트 PASS마다 1커밋(게이트명+테스트결과) / 런로그 누적.
> 선행: alembic head = f2b4d6e8a0c1, 베이스라인 **637 passed** 확인. 불일치 시 STOP.

---

## 게이트 A — 챗 cause/action 코드 현지화
목표: insight의 cause·action 코드(snake_case)가 **비영어 로케일에서 raw로 노출되지 않도록** 7개어(en/ko/zh/es/vi/th/pt) 라벨 제공.

작업:
- 엔진 rules의 `causes` / `recommended_actions`에 쓰이는 코드 문자열 전수 추출(레지스트리/grep). 목록을 런로그에 출력(개수 포함).
- 렌더러(`api/app/engine/renderer.py`) 라벨맵 또는 `src/messages/*.json`에 코드별 7개어 라벨 추가. 기존 en/ko 라벨 있으면 그걸 기준으로 zh/es/vi/th/pt 확장.

인수조건(머신 판정):
1. 추출된 cause/action 코드 **전체가 7개 언어 전부에 라벨 존재**(누락 0). 누락 목록이 비어야 PASS.
2. 샘플 finding을 비영어 로케일로 렌더 → 출력에 `^[a-z][a-z0-9_]*_[a-z0-9_]+$` 형태 raw 코드 **0건**(정규식 미매치).
3. `cd api && uv run pytest tests/ -q` → 637+ green, fail/error 0.
4. (프론트 메시지 수정 시) `cd src && npx tsc --noEmit` 0 + 7개 파일 키 패리티(누락 0).
가드레일: 번역은 i18n(텍스트)일 뿐 — KPI/수치 생성 아님. 기존 용어/톤 따름. 코드값 자체 변경 금지.
FAIL: STOP+로그(누락 코드·언어 목록). PASS: 커밋.

---

## 게이트 B — D-7 원화누수 게이트 (KR 전용 분리)
> D-7 확정: 출시 전 KR 전용 분리, 통화 일반화 P2. **확정 명시 없으면 STOP** — 본 문서가 확정 근거.
목표: `loss.py`의 KRW 경제값 룰(`SOW_RESIDUAL_*`/`SOW_SALVAGE_*` 기반, 예: `loss.sow_culling`)이 **country='KR'일 때만 발화**. 非KR 농장은 해당 손실액 룰 침묵.

작업:
- `api/app/engine/rules/loss.py`에서 SOW_RESIDUAL/SOW_SALVAGE(KRW) 사용 룰에 `ctx.country == "KR"` 게이트 추가. 보편 KPI(ABORTION/RTS/HIGH_PARITY/BORN_ALIVE/WEANING_* 등)는 글로벌 유지(건드리지 말 것).
- 어느 룰을 게이트했는지 런로그에 명시.

인수조건(머신 판정):
1. 테스트: ctx.country='US' + SOW_RESIDUAL/SALVAGE 입력 주입 → 해당 KRW 손실액 룰 발화 **0건**.
2. 테스트: ctx.country='KR' + 동일 입력 → 해당 룰 발화 **유지**(기존과 동일).
3. 보편 KPI 룰은 country 무관 발화 유지(회귀 테스트 green).
4. `uv run pytest tests/ -q` → 637+ green.
가드레일: 분리만(삭제·통화일반화 금지=P2). 값 변경 0.
FAIL: STOP+로그. PASS: 커밋.

---

## 게이트 C — PeriodLockedError 409→423 정리
목표: period_locks 잠금 기간의 이벤트 수정/삭제 시 **423** 일관 반환. 죽은 409 분기 제거.

작업:
- `PeriodLockedError` 처리부 확인. 409로 매핑되거나 도달불가한 분기가 있으면 423으로 통일/제거.
- 현재 live 동작이 이미 423이면 데드코드(409 매핑/주석) 제거만.

인수조건(머신 판정):
1. grep: `409`와 PeriodLock 연관 경로 **0건**(또는 의도적 잔존 시 사유 로그).
2. 통합테스트: 잠긴 기간 mating/farrowing/weaning 수정·삭제 → **HTTP 423** 반환(테스트로 확인). 신규 또는 기존 테스트 green.
3. `uv run pytest tests/ -q` → 637+ green.
가드레일: 동작(423) 변경 없이 정리만. 다른 상태코드 영향 0.
FAIL: STOP+로그. PASS: 커밋.

---

## 제외 — M3 / F4 (사유: 통과기준 미정)
- **M3**(AI 방식 슬롯 시퀀스 검증)·**F4**(사인별 폐사 25 상한): "통과 기준"이 수치/조건으로 정의돼 있지 않음 → 무인 판정 불가. 스펙(목표·작업·**머신 판정 인수조건**) 확정 후 별도 게이트로. 오늘 밤 제외.

## 종료 리포트(런로그 말미)
- 게이트 A/B/C PASS/FAIL + 커밋 해시
- 게이트 A: cause/action 코드 수 · 언어별 누락 0 확인
- 게이트 B: 게이트한 룰 목록 · US 0발화/KR 유지 결과
- 게이트 C: 423 반환 확인 · 409 잔존 0
- 637 → 최종 통과 수 / 막힌 것 / 사람 판단 필요
