# Codex 독립검증 프롬프트 — 피그플랜 이관 파일럿 (Phase E)

> 개발(import + 조직/계정 + UAT + 수치검증) 완료 후, **Codex에 붙여넣어 독립 검증**.
> 목적: 구현자(Claude)와 다른 관점으로 정합성·안전성·방법론을 적대적으로 검증.

---

## 프롬프트 (복붙)

PigOS 리포(`c:/dev/PigOS`)에서 피그플랜(Oracle)→PigOS(PostgreSQL) 이관 파일럿을 **독립 검증**해줘.
구현을 신뢰하지 말고 **반증 우선**으로 접근해라. 아래 파일을 읽고 각 항목을 확인 후, 발견을 심각도(CRITICAL/WARNING/INFO)로 분류해 보고해라.

### 검증 대상 파일
- `api/scripts/import_pigplan.py` — 이관 임포터(서비스레이어 replay)
- `api/scripts/setup_pilot_orgs.py` — 조직/계정 구성
- `api/app/services/event_service.py` — `record_weaning`의 `import_mode` 플래그(diff 확인)
- `tests/db/pigplan_import_mapping.md` — 코드/필드 매핑
- `tests/db/pigplan_schema_dump.md` — Oracle 실스키마·코드사전
- `tests/db/extract/*.csv` — 원본 추출

### 1. 매핑 정확성 (데이터 왜곡/날조 없음)
- STATUS_CD/사고구분(05)/교배방식/출하(08)/양자(16) 코드 매핑이 `pigplan_schema_dump.md` D절과 **정확히 일치**하는가? 잘못 매핑된 코드 있나?
- 분만: `born_alive=silsan, stillborn=sasan, mummified=mila` 순서가 맞나? (혼동 시 total_born·사산율 왜곡)
- `saengsi_kg`를 총중량으로 보고 `/born_alive`로 평균 산출 — CSV 실제값 분포로 총/평균 판별이 옳은가?
- 날짜 센티넬(9999)·범위(<1990,>=2100) 배제가 유효 데이터를 잘라내지 않나?

### 2. import_mode 안전성 (운영 무영향 증명)
- `record_weaning(import_mode=True)`가 우회하는 검증 목록을 나열하고, **기본값 False 경로가 이전과 바이트 동일**한지 diff로 확인해라.
- import_mode가 REST/모바일 sync에서 **호출될 경로가 전혀 없는지**(스크립트 전용) 확인. 유출 시 CRITICAL.

### 3. 이관 충실도 (누락/중복/캐스케이드)
- 합성 DEATH 주입(born_alive−weaned)이 **pre-wean 폐사율을 과대**하지 않나?(양자전출 포함분) 한계 명시.
- 격리(skip)된 이벤트가 PSY/NPD를 **체계적으로 편향**시키지 않나?(무작위 vs 특정연도 집중)
- `ear_tag=pig_no` 치환으로 실제 농장 태그 정보 손실 — rfid_tag 보존 확인.

### 4. 수치 정합성 방법론
- `calculate_psy`의 분모(월별 활성재고 평균)와 원본 raw(Σdusu) 비교가 **동치 비교**인가? 분모 정의 불일치 위험?
- 허용오차 ≤3%가 KPI 검증 기준으로 타당한가? 정확일치가 나온 연도의 우연성 배제?
- NPD(v_sow_npd) 정의가 피그플랜 NPD 정의와 같은가?(이유→교배 vs 비생산일 전체)

### 5. RBAC/보안 (setup_pilot_orgs.py)
- vendor_admin=4농장 / dealer=2농장 / owner=1농장 접근이 `get_accessible_farm_ids` 로직상 **실제로 보장**되나? 서브트리 CTE 깊이·org_level 설정 확인.
- 테스트 비번(`Pilot!2026`)이 코드/커밋에 하드코딩돼 운영 유출 위험은? 파일럿 격리 확인.
- 파일럿 조직/계정 고정 UUID가 운영 데이터와 충돌 가능성?

### 6. 실행 재현 (선택)
로컬 Docker `pigos` DB가 있으면: `pytest tests/pilot/` 실행 결과와 UAT 매트릭스가 문서 주장과 일치하는지 재현.

### 7. 이번 실행에서 나온 결과·수정 — 반증 대상 (★ 집중)
아래는 구현자가 "통과"라고 주장하는 실제 결과다. **각 주장을 반증**하려 시도해라.

**주장된 결과** (4농장 전량, ~17,900모돈):
- PSY 20~28(현실값) · 이유두수 diff 0~4.7% · NPD ±0.2일 · FR ±2pp · 무결성 위반 0 · UAT 전항목 PASS.

**반드시 반증 시도할 수정 5건**:
1. **PSY soft-delete 교정** (`import_pigplan.py` replay 후 `UPDATE sows SET deleted_at=exit_date`):
   - `out_dt`가 **없는** 퇴출모돈(약 8%: 848은 7435중 600만 exit_date 없음→활성)은 여전히 영구활성으로 분모 부풀림. PSY가 아직도 **소폭 과소**인가? 농장별 편향 방향 확인.
   - 재고 쿼리 `deleted_at IS NULL OR exit_date>=m` 에서 deleted_at=exit_date 세팅이 **경계월**(exit 당월) 이중계산/누락 없나?
2. **합성 DEATH 주입** (`born_alive-weaned`): 양자전출(FOSTER_OUT)분이 폐사로 오분류 → **pre-wean 폐사율 과대**. 이게 PSY엔 무관하나 mortality KPI 신뢰도엔? 한계 명시됐나?
3. **import_mode weaning 강제종료**: `remaining_after=0`로 사이클 항상 종료 → 부분이유·재이유가 사라져 **산차/WEI(NPD) 편향**? NPD가 ±0.2일로 맞는 게 우연인지 검증.
4. **스코어카드 재보정** (`verify_pilot.py` 교배 gap 게이트 제외): 분만 gap ~8%(격리)는 여전히 strict(2%)로 남겨 정직하게 FAIL 노출. **교배 제외가 실제 데이터 손실을 은폐**하지 않나? 분만 8% 격리의 원인(어떤 사이클이 빠지는지)과 PSY 편향 방향.
5. **uuid5 계정 UUID** (`pilot_common.user_uuid`): 네임스페이스 충돌·운영 계정과 겹칠 가능성.

### 산출물
- 심각도별 발견 목록(파일:라인 + 근거 + 재현/반례).
- **CRITICAL 0건**이면 "이관 파일럿 검증 통과", 아니면 수정 필요 항목 우선순위.
- 특히 "수치가 맞아 보이지만 방법론 결함으로 우연히 맞은" 케이스를 집요하게 찾아라
  (예: NPD ±0.2일이 import_mode 사이클 종료 때문에 우연히 수렴한 것 아닌지).
