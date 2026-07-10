# Codex 검증 프롬프트 — 피그플랜 숨은 룰의 PigOS 반영

> 개발자(Claude)가 "PigOS가 피그플랜 숨은 도메인 룰과 정합"이라 주장한다. **반증 우선**으로 독립검증하라.
> 그대로 Codex에 붙여넣기.

---

## 프롬프트 (복붙)

PigOS 리포(`c:/dev/PigOS`)에서, 피그플랜 숨은 도메인 룰이 PigOS 이관·서비스로직에 **정확히 반영됐는지 독립검증**해라. 구현자의 "정합" 주장을 신뢰하지 말고 **반례를 찾아라**. 심각도(CRITICAL/WARNING/INFO)로 보고.

### 읽을 것
- `tests/db/pigplan_business_rules.md` (룰 카탈로그 + "★ PigOS 대조 결과" 섹션 = 검증 대상 주장)
- `api/app/services/event_service.py` (record_mating/farrowing/weaning/reproductive_event, apply_terminal_reproductive)
- `api/scripts/import_pigplan.py` (이관 임포터)
- `api/app/services/kpi_service.py` (calculate_psy 등)
- `docs/specs/2026-07-10_lactating-cull-piglet-rule.md`

### 검증 항목 (각 주장을 반증 시도)

**1. STATUS_CD 파생 (구현자 주장: import가 STATUS_CD 무시하고 이벤트 replay로 파생)**
- 임포터가 정말 `TB_MODON.STATUS_CD`를 안 쓰나? 쓰는 경로가 하나라도 있으면 지적.
- WK 이벤트 없는 모돈(순수 마스터行)의 최종 status가 GILT로 고정돼 임신/포유 모돈이 GILT로 잘못 들어가지 않나? 그 비율·KPI 영향.
- 유산(010007)/사고(010006) 구분이 replay 후 ACCIDENT로 뭉개져 손실되나? RTS율·사고분석에 영향?

**2. 산차=분만시 증가 (주장: farrowing에서만 +1, mating은 미변경)**
- `record_farrowing`의 `sow.parity+=1`이 **중복 증가**(재분만·부분분만·오류 replay)로 과대되지 않나?
- import가 초기 `parity=in_sancha`로 시작 → GILT인데 parity>0인 모순. 산차별 성적 리포트가 왜곡되나?
- 재발정(RTS) replay가 parity를 건드리는 경로가 없나? BreedingCycle.parity와 sow.parity 불일치 가능성.

**3. 채번 경쟁조건 (주장: PigOS는 uuid라 MAX+1 레이스 없음)**
- 정말 농장스코프 MAX+1/COUNT+1 채번이 **어디에도** 없나? ear_tag/그룹코드/배치번호 생성 경로 전수. (grep 회피된 곳 주의)
- 동시 온보딩·동시 sow 등록 시 `UNIQUE(farm_id, ear_tag)` 위반 재시도 처리 있나, 아니면 500?

**4. 고아 데이터 gap 3종 (주장: 부분 반영, go-forward 대기)**
- 임포터의 합성DEATH가 **양자전출(FOSTER_OUT)을 폐사로 오분류** → pre-wean 폐사율·자돈정합 왜곡. 크기 추정.
- `AUTO_GB='Z' & 160004 & IO_PIG_NO NULL`(cull 자돈미아) 미replay → PigOS 자돈 카운트가 피그플랜과 **체계적으로** 어긋나나? 합성폐사 상쇄가 실제로 균형 맞나(수치 반례)?
- PigOS delete 로직(record_* 삭제/롤백)이 reciprocal 양자행·빈 그룹을 남기나? (go-forward gap 재현)

### 추가 스윕
- `pigplan_business_rules.md`의 🔶(부분확인) 룰 중 PigOS에 **미반영**인데 KPI/정합에 영향 주는 것 발견.
- 농장설정 상속(140022 총산 자동생성)·양자=재포유 동일코드·EDATE sentinel 등이 import에서 누락됐나.

### 산출물
- 심각도별 발견(파일:라인 + 근거 + 재현/반례).
- "정합이라 주장하나 실제로 어긋나는" 케이스 집중. CRITICAL 0 = 룰 반영 통과.
