# PigOS 전수 데이터 정합성 감사 — 자율 실행 프롬프트

> 사용법: 새 Claude Code 세션(작업 디렉터리 `C:\dev\pigos`)에 아래 **[프롬프트]** 전체를 붙여넣고 실행.
> 목적: 퇴근 전 무인 실행 → 전 농장 데이터 정합성을 결정적으로 검사하고 보고서를 남긴다.
> 절대원칙: **데이터를 자동수정하지 않는다. 수치를 추정·날조하지 않는다.** 위반은 근인만 분류·보고.

---

## [프롬프트] (이 아래 전체를 복사해서 붙여넣기)

당신은 PigOS 데이터 정합성 감사관이다. 아래를 순서대로, 무인으로 수행하고 마지막에 한국어 보고서를 남겨라.
**철칙: 어떤 DB 데이터도 수정/삭제하지 마라. 어떤 수치도 추정·검색·날조하지 마라. 위반은 근인 분류와 보고까지만.**

### 0. 전제 확인
- 로컬 백엔드가 떠 있어야 한다: `curl -s -m4 -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/docs` 가 200인지 확인.
  200이 아니면: `cd C:\dev\pigos\api && .venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000` 를 백그라운드로 띄우고 200 될 때까지 대기.
- PostgreSQL(pigos 개발 DB)이 살아있어야 한다(백엔드가 200이면 DB도 OK).

### 1. 결정적 전수 감사 (핵심)
```
cd C:\dev\pigos\api
PYTHONIOENCODING=utf-8 PYTHONPATH=. .venv/Scripts/python.exe scripts/integrity_audit.py
```
이 스크립트는 전 활성 농장을 돌며 검사한다(전부 실 집계 기반, 날조 0):
- **A** farrowing_rate: dashboard 출력 == farrowings/matings*100 (소수 일치) + percent 스케일
- **B** trend farrowing_rate 전부 percent(0~100) 범위
- **C** B1 항등식: 모든 분만 total_born == born_alive + stillborn + mummified
- **D** 두수 보존: 모든 분만 sum(weaned) <= born_alive + foster_in - foster_out - deaths
- **E** 음수/범위 이상치(PSY 0~45, NPD>=0, FR 0~100, 분만 두수 음수 0)
- **G** soft-delete 누수(삭제 분만/교배가 올해 KPI 집계에 미포함)

### 2. 결과 해석 (이 분기를 정확히 따를 것)
스크립트 종료코드와 `=== 결과: 검사 N건, 실패 M건 ===` 줄을 본다.

- **실패 0건** → 정합성 무결. 3번으로.
- **실패가 있으나 전부 `Test Farm`(농장 id `5ee6b97d`)** →
  이것은 **알려진 QA 시드 농장의 테스트 잔류 오염**이다(B1 validator·B4 보존검증 도입 전 누적분, 또는 DB 직접삽입분). production 아님.
  → 위반 건수(C/D 각각)만 집계해 보고. **데이터 건드리지 말 것.** "시드 농장 정리(reseed/삭제)는 사용자 결정 필요"라고 명시.
- **`Test Farm` 외 농장에 위반이 있거나, 새로운 유형의 위반(예: soft-delete 누수 G, 음수 E, 스케일 A)** →
  **실제 정합성 사고일 수 있다. 멈추고 근인을 코드에서 조사하라**(데이터 수정 금지). 위반 농장·엔티티 id, 기대값 vs 실제값, 의심 코드 경로를 증거와 함께 보고.

### 3. 회귀 가드 (정합성 인접)
```
cd C:\dev\pigos\api
.venv/Scripts/python.exe -m pytest tests/ -q
```
- 512+ passed 기대. 실패 시 실패 테스트명·메시지를 보고.

### 4. 라이브 계약 스모크 (선택, 백엔드 떠있을 때)
- 시드 계정 로그인 → refresh 200 → 교배 생성 → mating_date PATCH 200 (P0 회귀 가드).
- 한 농장 dashboard farrowing_rate가 percent(>1, 데이터 있을 때)인지 + 같은 농장 trend와 동일 스케일인지.

### 5. 보고서 (한국어, 간결하게)
다음을 표/불릿으로:
- 감사 농장 수, 검사 건수, 실패 건수
- 실패 분류: [시드 오염(Test Farm)] vs [실제 사고(타 농장/신규유형)] — 후자가 있으면 최상단에 🔴로
- pytest 결과(통과/실패 수)
- P0 스모크 결과
- **권고**: 시드 오염은 "사용자 승인 후 reseed/정리", 실제 사고는 근인+제안 수정(코드)
- 데이터는 한 건도 수정하지 않았음을 명시

---

## 참고: 현재(2026-06-25) 기준선
- 활성 농장 102개. **101개 무결, `Test Farm`(5ee6b97d)만 위반** ~405건(B1 항등식·보존 위반 분만 ~200행).
  → 이건 QA 시드 오염으로 확인됨. 타 농장·신규유형 위반이 새로 뜨면 그게 진짜 신호.
- farrowing_rate는 percent(0~100) 단일 SSOT(2026-06-25 통일). dashboard/trend/benchmarks/reports 동일 스케일.
