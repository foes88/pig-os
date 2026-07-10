# 피그플랜 숨은 도메인 룰 카탈로그 (PigOS 이관·구현 참조)

> 스키마만 봐선 안 보이는 **자동 cascade / 부수효과 / 상태전환 / 코드 의미** 룰 모음.
> PigOS는 이걸 ① 이관(replay) 시 재현하고 ② go-forward 로직에서 복제할지 개선할지 결정해야 함.
> 각 룰: **트리거 / 피그플랜 실제동작 / 이관 주의 / go-forward 권장**.
> 표시: ✅ 이번 세션 코드로 검증 · 🔶 부분확인(추가 스윕 필요)
> 생성: 2026-07-09 · 소스: pigplanxe(pmd/inputmd, pjd, sharing 매퍼·서비스)

---

## 코드 사전 (핵심 enum) ✅
- **모돈 상태 STATUS_CD (TC_CODE_SYS PCODE '01')**: `010001 후보돈` `010002 임신돈` `010003 포유돈` `010004 대리모돈` `010005 이유모돈` `010006 재발돈(사고)` `010007 유산돈(사고)` `010008 도폐사돈`
- **작업구분 WK_GUBUN (TB_MODON_WK)**: `A`전입 · `G`교배 · `B`분만 · `E`이유 · `F`사고. `DAERI_YN='Y'` = 대리포유(유모)
- **사고구분 SAGO_GUBUN_CD (TC_CODE_SYS PCODE '05')**: `050001`재발정 `050002`유산 `050003`도태 `050004`폐사 `050005`임돈전출 `050006`임돈판매 (050007~9 재발계열 세분)
- **자돈이벤트 GUBUN_CD (TB_MODON_JADON_TRANS)**: `160001`포유자돈폐사(생시도태) · `160002`부분이유 · `160003`양자전입=재포유 · `160004`양자전출
- **두수증감 (TJ_DUSU_MNG GUBUN_CD)**: `11`전입(SUB `110001`이유입식) · `12`전출 · `20`출하 · `033`폐사
- **수익 자동전표 AUTO_GB (TM_ETC_TRADE)**: `985004`도폐사모돈 · `985005`도폐사(도폐사판매 화면)
- **AUTO_GB (TB_MODON_JADON_TRANS)**: `A` = 전입 자동생성 · `Z` = **도폐사 자동생성**
- **수익 자동연동 (TM_ETC_TRADE AUTO_GB)**: `985005` = 도폐사돈 매출

---

## EVENT: 모돈 도폐사 (cull/death) ✅
**트리거**: 상태 `포유돈(WK_GUBUN=B)` 또는 `대리포유(E + DAERI_YN=Y)` 모돈을 도폐사
**피그플랜 실제동작** (`MdDiedSellWrMapper.updateDiedSellModon`):
1. 모돈 자동 **이유** 처리(TB_EU, DUSU=0) → 포유 종료
2. 포유자돈을 **양자전출(160004, AUTO_GB='Z')** 자동생성 (TB_MODON_JADON_TRANS)
3. 전출 대상 모돈(`youtPigNo`) 지정 시**에만** → 그 모돈에 양자전입(160003) 자동생성
**전출 대상 미지정("그냥 폐사")**: 자돈은 `IO_PIG_NO=NULL` 로 **전출만 되고 전입처 없음** → 폐사 아님, 다른 모돈에도 안 붙음 = **미아/손실 데이터**
**이관 주의**: `AUTO_GB='Z' AND GUBUN_CD='160004' AND IO_PIG_NO IS NULL` = destination 없는 전출. piglet_event(전출, dest=NULL, reason='sow_culled')로 명시 replay 안 하면 자돈수 정합성 깨짐.
**go-forward 권장**: 조용한 미아 방지 — cull 시 포유자돈 있으면 **전출대상 지정 강제 OR 자돈 폐사 명시** 중 택일하게 막기.
**취소**: `deleteDiedSell` 에서 AUTO_GB='Z' 레코드 삭제로 되돌림.

## EVENT: 웅돈 도폐사 ✅
**트리거**: 웅돈 도폐사/판매
**동작** (`TbUngdonMapper.updateTbUngdonDieAndSellMapper`):
- `TB_UNGDON` **UPDATE** (OUT_DT/OUT_GUBUN_CD/SALE_* 세팅). **DELETE 아님, USE_YN 유지**
- 수익연동 ON(etcTradeYn='Y')이면 `TM_ETC_TRADE` INSERT (AUTO_GB='985005', ACCOUNT_CD='512001')
**이관 주의**: 웅돈은 개체 1마리 — 자돈/양자 없음. "출하됨"은 `OUT_DT != 9999-12-31` 로 판정.
**취소**: OUT_* 리셋 + USE_YN='Y' 복구, TM_ETC_TRADE 해당행 USE_YN='N'.

## EVENT: 분만 (farrowing) — 총산 입력방식 ✅
**트리거**: 분만기록 입력, 농장설정 `140022`(총산 자동생성)에 따라 분기
**동작** (`MdChildbirthWr`):
- `140022='Y'` → 총산 = 미라+사산+실산 **자동계산**(입력칸 숨김, 실산 입력)
- `140022='N' 또는 미설정` → 총산 **수동입력**(정상 기본)
- 분만기록에서 양자전입/전출(junip/junchul) 직접 입력 가능 (농장설정 `140013` 양자상대모돈)
**이관 주의**: 원천의 총산/실산 값이 어느 방식으로 들어갔는지 농장별 상이. PigOS는 실산·미라·사산·양자 원천값 그대로 받아 총산 재계산 권장.

## EVENT: 양자 / 재포유 (foster) ✅
**핵심**: **양자전입(160003) = 재포유 = 같은 코드**. 받는 모돈 상태에 따라 라벨만 다름:
- B(받는 모돈 포유중) → 일반 양자전입
- E+DAERI_YN='Y'(이유 후 빈 모돈이 받음) → 재포유/대리포유(유모돈)
**포유중 판정 공식**: `WK_GUBUN='B' OR (WK_GUBUN='E' AND DAERI_YN='Y')`
**전출(A)/전입(Z) 쌍**: 도폐사 자동전출은 AUTO_GB='Z', 일반 전입은 'A'.

## EVENT: 자돈/비육 그룹 (grow-out) ✅
**EDATE sentinel**: 열린(미종료) 그룹 = `EDATE='9999-12-31'`, 종료 = 실제 종료일. **NULL이면 안 됨**(콤보/현황에서 사라짐).
**재고 공식**: `전입(11) − 전출(12) − 출하(20) − 폐사(033)`
**이관 주의**: 이관 시 EDATE 안 채우면 NULL → 그룹 조회 전멸 (실제 발생함). 원천 종료일을 EDATE로, 빈칸이면 9999-12-31.

## RULE: 농장설정 상속 (TC_FARM_CONFIG) ✅
**동작**: 농장에 설정 없으면 `TC_CODE_SYS` 마스터값(originValue) 상속. 로그인/농가변경 시 `mergeFarmInitSetMapper`가 빈값을 마스터로 채움.
**이관 주의**: 마스터 기본값이 잘못되면(예: 140022='Y') 미설정 농장이 전부 상속 → 대량 오작동. PigOS는 농장별 유효설정 = `NVL(농장값, 마스터값)`로 스냅샷.

## RULE: 상태 제약 ✅
- **도폐사돈(OUT_DT 있음)은 교배기록 불가** (`SharingFileDataValidation`).
- 교배 가능 상태: `E+DAERI_YN='Y'`(대리이유) / `G`(교배대기?) / `B` 등 (검증 로직 참조).

## RULE: 모돈 기록 소프트삭제 🔶
**동작**: 모돈 기록 삭제 = 물리삭제 아님, **USE_YN='N'** (6개 관련 테이블 flip으로 복구 가능).
**이관 주의**: `USE_YN='N'` 레코드는 이관 제외 or 삭제상태로 표시. 복구 이력 고려.

---

## ★ RULE: 모돈 상태(STATUS_CD)는 저장이 아니라 파생 ✅ (가장 중요)
**동작**: 교배/분만/이유/사고 저장은 **`TB_MODON.STATUS_CD`를 절대 UPDATE 안 함** — `TB_MODON_WK`에 행만 append. 라이브 상태는 **최신(MAX SEQ) WK_GUBUN으로 실시간 파생** (`PmdCommonModonMapper.xml:59-70`):
- WK 없음 → 저장된 STATUS_CD(후보돈 등) · `G`→임신 · `B`→포유 · `E`&DAERI='N'→이유모돈 · `E`&DAERI='Y'→대리모 · `F`&SAGO='050002'→유산 · `F`&기타→사고
- STATUS_CD를 **쓰는 곳은 오직 전입/import(기본 010001)·전입수정·기초수정 3곳뿐** (일상 이벤트 아님).
**숨은 보정**: 리포트마다 반복 — **"임신돈(010002)이지만 IN_SANCHA=0 AND IN_GYOBAE_CNT=1 이면 후보돈(010001)으로 간주"** (`SharingCommonMapper.xml:57` 외 4곳).
**이관 주의**: **진실원천 2개** — 대시보드/모바일 리포트는 저장 STATUS_CD 직접 읽고, 작업화면은 파생상태 사용 → import 후 STATUS_CD stale. PigOS가 status를 명령형 컬럼으로 두려면 **최신 이벤트 파생과 항상 일치**시켜야. 유산(010007)/사고(010006) 구분 유지 필수.

## RULE: 산차(SANCHA)·교배차수 채번 ✅
- **산차는 분만(B) 시점에만 +1** — `SANCHA=MAX+1` (`TbModonWkMapper.xml:8-20`). 교배/사고/이유는 유지. **재발정은 산차 소비 안 함**(같은 산차 내 교배차수만 증가).
- **교배차수 GYOBAE_CNT**: `G`→현산차 MAX+1, `B`→0 초기화 (`:85-87`).
**이관 주의**: parity 증가를 교배시점으로 구현하면 산차별 성적 왜곡. 반드시 farrowing에서 증가.

## RULE: 작업 SEQ 채번 + 삭제 시 재정렬 ✅
- `SEQ = NVL(MAX(SEQ),0)+1 WHERE FARM_NO=? AND PIG_NO=? AND USE_YN='Y'` (개체단위 누적).
- **삭제 시**: 삭제SEQ보다 큰 행을 MERGE로 -1씩 당겨 **SEQ 연속성 복구** (교배/사고/분만/이유 공통 패턴, `MdMatingWrMapper.xml:365-385`).
**이관 주의**: `USE_YN='Y'` 스코프 MAX+1은 soft-delete 후 재등록 시 SEQ 충돌 소지. 파생·이전작업(SEQ-1) 조인이 연속성에 의존 → PigOS가 gap 허용 키로 가면 그 조인들 재작성 필요.

## EVENT: 사고 / 재발정 / 유산 (TB_SAGO) ✅
**저장 = 이중기록**: 한 트랜잭션에 `TB_MODON_WK`(WK_GUBUN='F') + `TB_SAGO`(SAGO_GUBUN_CD) 동시 (`MdPregnancyWrMapper.xml:302-333`). 단일테이블 아님.
**종류별 부수효과**:
- **재발(050001)/유산(050002)** → 모돈 생존(OUT_DT 안 건드림, 유산 OUT_DT UPDATE는 주석처리 미실행), 차기 교배대기로 파생복귀.
- **도태/폐사/전출/판매(050003~6)** → `mergeModonJobGroupEndMapper` 호출 → 진행중 없으면 `TB_MODON_GRP` 종료(END_TYPE='euEnd'). 재발/유산엔 미호출.
- **도폐사/판매 전환** → OUT_DT/OUT_GUBUN + WK(AUTO_GB='Z') + TB_SAGO + **수익 자동전표 TM_ETC_TRADE(AUTO_GB='985004' 도폐사모돈) MERGE** (cjpig 제외).
**삭제**: TB_SAGO+WK 삭제 + SEQ 재정렬. 가드 = `OUT_DT='99991231' AND MAXSEQ=SEQ`(마지막 이벤트 & 미출하만). ⚠️ **그룹종료(050003~6)의 되돌림(그룹 재오픈)은 삭제경로에 미발견 → 비대칭, 고아 열린그룹 위험.**
**이관 주의**: "임신사고=출하" 아님. 도폐사/판매엔 자동전표(985004) 딸림 — 재현 누락 쉬움.

## EVENT: 이유 (TB_EU) → 비육그룹 조건부 자동편입 ✅
**저장 다중기록** (오케스트레이션은 `MdWeaningWrServiceImpl.java`, DB트리거 아님):
1. `TB_MODON_WK`(E) → 2. `TB_EU`(DUSU/ILRYUNG/TOTAL_KG/DAERI_YN) → 3. (선택)`TB_PIG_FEED`
- **비육편입은 조건부**: `grpNo>0` 또는 `-9999`(자동생성)일 때만.
  - 자동생성(-9999): `TJ_GAIN_GRP` INSERT, `JU_GUBUN='J'`, **모돈품종(코드'041')→비육품종(코드'043') 자동변환**, GRP_ID=`'G'+이유일yyyymmdd+'-'순번`.
  - **실제 두수편입 = `TJ_DUSU_MNG` 전입행(GUBUN_CD='11'/SUB='110001' 이유입식)** — TJ_GAIN_GRP 아님.
- 포유중 손실/양자/재포유 두수는 TB_EU 아니라 **TB_MODON_JADON_TRANS**로 분해: 폐사 `160001`·양자전입 `160003`·전출 `160004`·재포유(DAERI='Y'시 `160003`). `BUN_DT IS NULL` = 이유발 등록 식별자.
- **대리모(DAERI='Y')**: 신규 이유해도 모돈그룹 종료 미실행 — 계속 포유중.
**삭제**: TB_EU/JADON_TRANS(BUN_DT NULL분)/TJ_DUSU_MNG 이동행 삭제 + WK 삭제. ⚠️ **TJ_GAIN_GRP 껍데기는 안 지움 → 고아 빈그룹 잔존.**
**이관 주의**: "이유=무조건 비육편입" 오해 금지. 편입 실체는 TJ_DUSU_MNG 전입행. TB_MODON_GRP(모돈배치) ≠ TJ_GAIN_GRP(비육돈군).

## EVENT: 분만 저장/삭제 Cascade ✅
**저장 = 3~4테이블**: `TB_MODON_WK`(B, SANCHA=MAX+1, GYOBAE_CNT=0) + `TB_BUNMAN`(SILSAN/MILA/SASAN/생시KG) + `TB_MODON_JADON_TRANS`(생시도태 160001 / 양자 160003·160004, `BUN_DT=wkDt, EU_DT=NULL`) + **양자 상대모돈 reciprocal INSERT**.
- **총산(CHONG_SAN) 컬럼 없음** — `SILSAN+MILA+SASAN` 파생. 설정 140022는 UI 입력방식 토글일 뿐(기본 'N').
**삭제 = SANCHA 단위 통삭제 (하드 DELETE, 순서 고정)** (`MdChildbirthWrServiceImpl.java:210-213`): ①`TG_BUN_JADON` → ②`TB_MODON_JADON_TRANS`(iuFlag='D'라 GUBUN_CD 불문 **생시도태·양자·부분이유 전부**) → ③`TB_BUNMAN` → ④`TB_MODON_WK`(+SEQ 재정렬).
- 가드: `MAX_GUBUN='Y'(마지막작업) AND DIE_OUT_YN!='Y' AND AUTO_GB!='A'` → **후속작업 있으면 삭제 차단**.
**이관 주의**: GUBUN_CD별이 아니라 **SANCHA 통삭제**, 전부 하드DELETE. ⚠️ **양자 상대모돈 reciprocal 행은 미정리 → 상대에 고아 양자행 잔존(실제 gap)** — PigOS에서 reciprocal cleanup 추가 필요.

## RULE: 개체번호 채번 = MAX+1 농장스코프 (시퀀스 아님) ✅
- PIG_NO/JADON_PIG_NO/GRP_NO 모두 `NVL(MAX(...),0)+1 WHERE FARM_NO=?`. 도메인 데이터에 Oracle 시퀀스 **전무**.
  - PIG_NO(모돈/웅돈): **USE_YN 무관 전체 MAX**(삭제행 포함, 번호 재사용 방지).
  - JADON_PIG_NO: VALUES 인라인 서브쿼리 — **배치 INSERT 시 동일값 위험**.
- **IGAK_NO / FARM_PIG_NO / RFID_NO = 자동채번 아님, 사용자 입력**. RFID 'UNDEFINED' 레거시값 → 조회 시 `NVL(NULLIF(RFID_NO,'UNDEFINED'),' ')` 치환.
**이관 주의**: 농장별 MAX+1은 **동시 등록 시 PK 경쟁조건** → PigOS는 농장별 시퀀스 or `UNIQUE(farm_no, no)`+재시도. "농장별 순번"이 사용자 가시번호라 전역시퀀스로 바꾸면 화면번호가 바뀜. RFID UNIQUE 신규부여 시 기존 중복/UNDEFINED/대소문자혼재로 제약위반 → 마이그레이션 정제 필요.

## EVENT: 정산 배치 (settlement) ✅
- **정산일 게이트**: 오늘이 농가 `BILL_DAY`(또는 말일)일 때만 수집 — 매일 도는 게 아님. `STOP_DT` active 농장만(`TA_FARM` STOP_DT BETWEEN SYSDATE AND '9999-12-31').
- 예외 삼킴: `e.printStackTrace()`만, 실패가 표면에 안 뜸. `@Transactional` 전체 롤백.
**이관 주의**: 정산은 스냅샷 이벤트라 PigOS 번식 replay와 별도 도메인. 이관 필수 아니면 제외 가능.

---

## 미발견 / 추측 (코드만으론 확정 불가)
- 050007/8/9 사고구분 한글명, RFID/IGAK/FARM_PIG_NO **DB UNIQUE 제약 여부** — 스키마/TC_CODE_SYS 확인 필요.
- 사고 삭제 시 종료그룹(TB_MODON_GRP) **재오픈 미발견**(비대칭 gap).
- 분만경로 양자 `AUTO_GB` 명시세팅 미발견('Z'는 도폐사전환 경로에서만).
- 초발정은 별도 후보관리 화면 — 상태파생과 무관(확인됨).

> 근거 file:line은 pigplanxe 리포 기준. PigOS 반영 시 각 룰의 **이관 주의** 우선.

---

## ★ PigOS 대조 결과 (2026-07-10, 정합성 직결 4종)

| 룰 | PigOS 상태 | 근거 |
|---|---|---|
| **STATUS_CD 파생** | ✅ 정합 | 임포터가 `TB_MODON.STATUS_CD` 무시 → sows.status=`GILT` 초기화 후 `record_mating/farrowing/weaning/reproductive_event` replay로 상태 파생. 저장 STATUS_CD의 stale 문제 원천 회피. |
| **산차=분만시 증가** | ✅ 정합 | `event_service.record_farrowing` 에서 `sow.parity += 1`. `record_mating`은 BreedingCycle의 예정 parity(`sow.parity+1`)만 세팅, sow.parity 미변경. RTS는 parity 소비 안 함(교배 미발생). |
| **채번 경쟁조건** | ✅ 무해 | PigOS는 모든 PK가 uuid4, ear_tag=사용자입력(import는 pig_no). 농장스코프 MAX+1 채번 없음(grep 0건) → Oracle의 PK 레이스·JADON 배치충돌 구조적 부재. |
| **고아 데이터 gap 3종** | 🔶 부분 | (a) 자돈미아(포유 cull): 임포터가 KPI목적상 합성DEATH로 카운트균형 + 룰스펙(`docs/specs/2026-07-10_lactating-cull-piglet-rule.md`)로 go-forward 검증 설계. (b) 분만삭제 reciprocal 양자행·(c) 이유삭제 빈 TJ_GAIN_GRP: 피그플랜 **삭제 cascade** gap → import(활성행만)엔 무영향, PigOS delete 로직에 reciprocal cleanup 추가 필요(go-forward). |

**이관 임포터 알려진 한계** (KPI PSY/NPD 목적 우선):
- 양자/포유폐사(TB_MODON_JADON_TRANS)를 개별 replay 안 하고 이유 시 `(born_alive−weaned)` 합성DEATH로 근사 → PSY 정확, pre-wean 폐사율은 근사(양자전출 포함).
- `AUTO_GB='Z' & 160004 & IO_PIG_NO NULL`(cull 자돈미아) 명시 replay는 미구현(카운트는 합성폐사로 상쇄). 정밀 자돈추적 필요 시 확장.

**go-forward 반영 대기**: 포유 cull 자돈처리 검증(룰스펙 ②), 분만삭제 reciprocal cleanup, 이유삭제 빈그룹 정리.
