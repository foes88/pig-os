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
- **사고구분 SAGO_GUBUN_CD (TC_CODE_SYS PCODE '05', 운영DB 검증)**: `050001`**(구)재발불임(레거시)** · `050002`유산 · `050003`도태 · `050004`폐사 · `050005`임돈전출 · `050006`임돈판매 · `050007`**공태** · `050008`**재발** · `050009`**불임** — 이관 시 050001(구코드)과 050007~9(현행 세분)가 혼재하므로 둘 다 매핑 필요
- **자돈이벤트 GUBUN_CD (TB_MODON_JADON_TRANS, 운영DB 검증)**: `160001`포유자돈폐사 · `160002`부분이유 · `160003`양자전입=재포유 · `160004`양자전출
- ⚠️ **SUB_GUBUN_CD 네임스페이스 충돌**: `TB_MODON_JADON_TRANS.SUB_GUBUN_CD`의 `'050001'`은 코드 주석상 **"산자수"** — TC_CODE_SYS '05'(=(구)재발불임)와 **코드는 같고 의미가 다른 별도 사전**. PigOS는 SUB_GUBUN_CD를 '05' 사고사전으로 해석하면 안 됨(정확한 사전은 미확정, 컨텍스트별 해석 필요)
- **두수증감 (TJ_DUSU_MNG GUBUN_CD)**: `11`전입(SUB `110001`이유입식) · `12`전출 · `20`출하 · `033`폐사
- **수익 자동전표 AUTO_GB (TM_ETC_TRADE)**: `985004`=**모돈** 도폐사 · `985005`=**웅돈** 도폐사. 생성조건은 **경로별로 다름 (공통조건 아님!)**:
  - 임신사고→도폐사 전환: `etcTradeYn='Y'` **AND** `sysEnv!='cjpig'` (`MdPregnancyWrMapper.xml:402-405`)
  - 모돈 도폐사 화면: `etcTradeYn='Y'` 만 — **생성부에 cjpig 가드 없음**, cjpig 가드는 삭제경로(:927-935)에만 (`MdDiedSellWrMapper.xml:530`)
  - 웅돈 도폐사: `iuFlag='I'` + `etcTradeYn='Y'` 만 — 생성부 cjpig 가드 없음, 삭제경로(:352-360)에만 (`TbUngdonMapper.xml:207-249`)
  - ⚠️ 생성/삭제 가드 비대칭: cjpig 환경에서 화면 생성은 가능하나 취소 시 전표 삭제가 스킵됨 → 고아 전표 가능성(레거시 gap)
- **사고코드 050001 신규입력 차단**: 서버 검증에서 `050001`(구)재발불임 선택 시 저장 거부(msg.064 "재발/불임 중 선택") — `DataValidationChk.java:522`. 기존 데이터에만 존재하는 레거시 코드
- **AUTO_GB (TB_MODON_JADON_TRANS)**: `A` = 전입 자동생성 · `Z` = **도폐사 자동생성**
- **수익 자동연동 (TM_ETC_TRADE AUTO_GB)**: `985005` = 웅돈 도폐사 매출

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
**취소**: `deleteDiedSell` 은 **도폐사 모돈 자신의 자동 전출행(160004, AUTO_GB='Z')만 삭제** (`MdDiedSellWrMapper.xml:891-897`). ⚠️ **전출대상 모돈에 생성됐던 reciprocal 양자전입(160003) 행은 미정리** — 취소 후 대상 모돈에 고아 전입이 남아 포유재고 부풀림 (고아 gap ④).

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
**AUTO_GB 표기**: 도폐사 자동생성 쌍(전출 160004 + reciprocal 전입 160003)은 둘 다 `AUTO_GB='Z'`, 전입 시 자동생성은 `'A'`.

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
- **파생 로직이 이중 구현**: 매퍼 내 CASE식 + **DB 저장함수 `SF_GET_MODONGB_STATUS`(WK_GUBUN, SAGO_GUBUN_CD, OUT_DT, STATUS_CD, DAERI_YN → 상태)** — 7개 매퍼에서 사용. PigOS는 단일 파생 함수로 통합하되 두 구현의 의미가 같은지 검증할 것.
**숨은 보정** (재검증 2차 — 쿼리별 편차 있음): "STATUS_CD='010002'(임신돈) AND IN_SANCHA=0 AND IN_GYOBAE_CNT=1 → 후보돈(010001) 간주" 보정이 존재하나 적용 조건이 쿼리마다 다름 —
- 대표 상태파생 쿼리: **작업이력 없는(WK 미존재) 모돈에만** 적용 (`SharingCommonMapper.xml:51-61`)
- 월경영 집계 쿼리: **작업이력 조건 없이** 같은 필드조합에 무조건 적용 (`MonthMdAnyWrMapper.xml:21`)
→ PigOS는 한 가지 규칙으로 통일하되(WK 부재 시로 권장), 레거시 수치와 대사할 땐 이 편차를 감안할 것.
**이관 주의**: **진실원천 2개** — 대시보드/모바일 리포트는 저장 STATUS_CD 직접 읽고, 작업화면은 파생상태 사용 → import 후 STATUS_CD stale. PigOS가 status를 명령형 컬럼으로 두려면 **최신 이벤트 파생과 항상 일치**시켜야. 유산(010007)/사고(010006) 구분 유지 필수.

## RULE: 산차(SANCHA)·교배차수 채번 ✅
- **산차는 분만(B) 시점에만 +1** — `SANCHA=MAX+1(USE_YN='Y' 범위)` (`TbModonWkMapper.xml:9-20`). 교배/사고/이유는 화면 전달값 유지. **재발정은 산차 소비 안 함**(같은 산차 내 교배차수만 증가).
- **교배차수 GYOBAE_CNT**: `G`→현산차 MAX+1 · `B`→0 초기화 · 그 외 유지 (`:85-92`).
- **첫 작업 승계**: 작업이력이 0건이면 교배차수를 `TB_MODON.IN_GYOBAE_CNT`(전입 시 교배차수)에서 승계 (`:44-52`) — 임신 상태로 전입한 모돈의 이어달리기.
- **WK_DT 이중저장**: `WK_DT`=**VARCHAR 'YYYYMMDD'** + `WK_DATE`=DATE 두 컬럼에 같은 값 (`:81-84`). 이관 시 타입 함정(문자 정렬·포맷 불일치) 주의.
**이관 주의**: parity 증가를 교배시점으로 구현하면 산차별 성적 왜곡. 반드시 farrowing에서 증가.

## RULE: 차기 예정일 파생 (모돈 리스트/알림) ✅
**동작**: 최신 작업 기준 —
`G`(교배)→WK_DT+**임신기간** · `B`(분만)→+**포유기간** · `E`&대리N(이유)→+**재귀기간** · **`E`&대리Y(대리모)→+포유기간(재귀 아님!)** · 작업없는 후보돈(010001)→기준일+**초교배기간**.
기간값은 농장설정(`TC_FARM_CONFIG` — 운영DB 명칭: 140002 **평균임신기간**·140003 **평균포유기간**·140007 **후보돈초교배일령**·140008 **평균재귀일**)에서.
⚠️ **후보돈 기준일이 구현마다 다름 (레거시 비일관)**:
- `PmdCommonModonMapper.xml:78` → 단순 `IN_DT`
- `MdCommonMapper.xml:123,154-160` → **`GREATEST(NVL(LAST_WK_DT,1900-01-01), IN_DT)`** (전입 최종작업일 우선)
**이관 주의**: PigOS는 GREATEST 쪽(더 정교)으로 통일 권장하되, 어느 화면과 대사하느냐에 따라 예정일이 다르게 보일 수 있음을 인지. 같은 농장설정 파라미터를 읽어야 화면 예정일 일치.

## RULE: 작업 SEQ 채번 + 삭제 시 재정렬 ✅
- `SEQ = NVL(MAX(SEQ),0)+1 WHERE FARM_NO=? AND PIG_NO=? AND USE_YN='Y'` (개체단위 누적).
- **삭제 시**: 삭제SEQ보다 큰 행을 MERGE로 -1씩 당겨 **SEQ 연속성 복구** (교배/사고/분만/이유 공통 패턴, `MdMatingWrMapper.xml:365-385`).
**이관 주의**: `USE_YN='Y'` 스코프 MAX+1은 soft-delete 후 재등록 시 SEQ 충돌 소지. 파생·이전작업(SEQ-1) 조인이 연속성에 의존 → PigOS가 gap 허용 키로 가면 그 조인들 재작성 필요.

## EVENT: 사고 / 재발정 / 유산 (TB_SAGO) ✅
**저장 = 이중기록**: 한 트랜잭션에 `TB_MODON_WK`(WK_GUBUN='F') + `TB_SAGO`(SAGO_GUBUN_CD) 동시 (`MdPregnancyWrMapper.xml:302-333`). 단일테이블 아님.
**종류별 부수효과**:
- **재발계열(050001구·050007공태·050008재발·050009불임)/유산(050002)** → 모돈 생존(OUT_DT 안 건드림, 유산 OUT_DT UPDATE는 주석처리 미실행), 차기 교배대기로 파생복귀. 상태파생은 050002만 유산돈, 그 외 F는 사고돈/재발돈.
- **도태/폐사/전출/판매(050003~6)** → `mergeModonJobGroupEndMapper` 호출 → 진행중 없으면 `TB_MODON_GRP` 종료(END_TYPE='euEnd'). 재발/유산엔 미호출.
- **도폐사/판매 전환** → OUT_DT/OUT_GUBUN + WK(AUTO_GB='Z') + TB_SAGO + 수익 자동전표 TM_ETC_TRADE(AUTO_GB='985004') MERGE — **단 `etcTradeYn='Y'`일 때만 + cjpig 제외** (`MdPregnancyWrMapper.xml:402-405`). "항상 생성" 아님.
**삭제**: TB_SAGO+WK 삭제 + SEQ 재정렬. 가드 = `OUT_DT='99991231' AND MAXSEQ=SEQ`(마지막 이벤트 & 미출하만). ⚠️ **비대칭**: 그룹 재계산(`mergeModonJobGroupEndMapper`)은 **양방향**(진행 0→닫기 END_DT=SYSDATE / 진행 생기면→재오픈 9999-12-31, `MdGroupWrMapper.xml:492-501`)인데 사고 **등록만 호출하고 삭제는 미호출**(`MdPregnancyWrServiceImpl.java:132` vs `:233`) → 사고삭제로 모돈이 다시 진행상태가 돼도 **그룹이 오종료(닫힌 채) 잔존**.
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
- RFID/IGAK/FARM_PIG_NO **DB UNIQUE 제약 여부** — 스키마 확인 필요.
- `TB_MODON_JADON_TRANS.SUB_GUBUN_CD`의 정확한 코드사전 (컨텍스트별: 도폐사 전출 시 '050001'="산자수" 주석, 생시도태(160001)의 사유코드 체계 등) — TC_CODE_SYS '05'와 별개.
- ~~사고 삭제 시 종료그룹 재오픈 미발견~~ → **확정됨(코드 확인)**: 사고 등록은 그룹 재계산 호출(`MdPregnancyWrServiceImpl.java:132`), `deletePregnancy()`(`:233`)는 삭제만 수행 — **그룹 재오픈 없음, 비대칭 확정**. PigOS는 사고삭제 시 그룹상태 재계산 추가 권장.
- 분만경로 양자 `AUTO_GB` 명시세팅 미발견('Z'는 도폐사전환 경로에서만).
- 초발정은 별도 후보관리 화면 — 상태파생과 무관(확인됨).

## 검증 이력
- v4 (2026-07-13): **codex 2차 리뷰(FAIL) findings 7건(P0 1 + P1 4 + P2 2) 전부 재검증 후 반영** — codex v4 재검증 최종 **PASS**(2026-07-13). — ① 985004/985005 생성조건 **경로별 3분리**(cjpig 가드는 사고→전환 경로만, 화면/웅돈 생성부엔 없음 + 생성/삭제 가드 비대칭 노트) ② 도폐사 **취소** 시 reciprocal 양자전입(160003) 미정리 → **고아 gap ④** 추가 ③ 사고삭제 결과 방향 정정: "고아 열린그룹"(오기) → **오종료(닫힌 채) 잔존** (merge는 양방향임을 명시) ④ AUTO_GB 표기 자체모순 수정 ⑤ 140002/140003/140007/140008 운영DB 명칭으로 정정(140003=평균포유기간) ⑥ `docs/db-table-relations.md §6.2` STATUS_CD 사전 전면 정정(010004=대리모돈 등) ⑦ PigOS 대조 섹션에 스코프 라벨(PigOS 세션 자체평가, codex 검증범위 밖).
- v3 (2026-07-13): **codex(외부모델) 교차리뷰 findings 반영** — 전 항목 메인세션 재검증 후 정정: ① 985004/985005 = 모돈/웅돈 구분 + `etcTradeYn='Y'`·cjpig 조건부 명시 ② 후보돈 보정의 쿼리별 편차(월경영은 무조건 적용) ③ 예정일 후보돈 기준일 구현 분기(IN_DT vs GREATEST) ④ 050001 신규입력 차단 룰 추가 ⑤ 사고삭제 그룹 재오픈 비대칭 file:line 확정 ⑥ 리포 문서 `docs/db-table-relations.md §6.6`의 050001/050002 오기(공태/재발) 정정 — PigOS는 구버전 그 문서를 참조하지 말 것.
- v1 (2026-07-09): 세션 내 직접 검증 룰 수록.
- v2 (2026-07-09): 서브에이전트 전체 스윕 + **메인 세션 재검증 패스** — 상태파생(62-70)·SANCHA/GYOBAE_CNT/SEQ(TbModonWkMapper)·분만삭제 순서/통삭제/가드·이유입식 110001·품종 041→043 CNAME매칭·후보돈 보정(조건 정밀화)·985004 MERGE·euEnd·그룹껍데기 잔존, 전부 실코드 확인. 코드값은 운영DB 추출 CSV(TC_CODE_SYS)로 교차검증 — **050001은 재발정이 아니라 (구)재발불임**으로 정정, 050007~9=공태/재발/불임 확정, 160001~4 확정.

> 근거 file:line은 pigplanxe 리포 기준. PigOS 반영 시 각 룰의 **이관 주의** 우선.

---

## ★ PigOS 대조 결과 (2026-07-10, 정합성 직결 4종)

> ⚠️ **스코프 주의**: 이 섹션은 **PigOS 세션의 자체평가**로, 근거(`event_service.record_farrowing`, `docs/specs/2026-07-10_lactating-cull-piglet-rule.md` 등)는 PigOS 리포에 있음 — **pigplan 워크스페이스(codex) 검증범위 밖**. 피그플랜 측 룰 서술의 PASS/FAIL과 무관한 참고 정보.
> 추가: 고아 gap은 이후 **4종으로 확장**됨 — (d) 모돈 도폐사 **취소** 시 전출대상 모돈의 reciprocal 양자전입(160003, AUTO_GB='Z') 미정리 (EVENT: 모돈 도폐사 § 취소 참조). PigOS cleanup 목록에 반영 필요.

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
