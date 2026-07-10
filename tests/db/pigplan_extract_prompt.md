# wiselake-console에 줄 프롬프트 — 피그플랜 Oracle 스키마 발견 (1단계)

> 이 프롬프트를 **wiselake-console 프로젝트의 Claude 세션**에 붙여넣으세요.
> (그쪽이 피그플랜 Oracle 읽기전용 접속권 + `pipelines/oracle_connector.py` 보유)
> 목적: PigOS로 데이터를 가져오기 전에 **실제 Oracle 스키마·코드값을 정확히 파악**한다.

---

## 프롬프트 (복붙)

피그플랜(PigPlan) 운영 Oracle DB의 스키마를 프로파일링해줘. 목적은 이 데이터를 PigOS(PostgreSQL) 신제품으로 이관하기 위한 매핑 설계다. `pipelines/oracle_connector.py`의 `query_df(sql)`(SELECT 전용, DataFrame 반환)을 사용해라. **절대 쓰기(INSERT/UPDATE/DELETE/MERGE/DDL) 금지, SELECT만.** 바인드 변수(`:x`)는 `query_df`에서 안 먹을 수 있으니, 테이블명은 Python f-string으로 직접 넣거나 리스트를 순회해라.

아래를 순서대로 조사하고, 결과를 **하나의 마크다운 파일** `c:/dev/PigOS/tests/db/pigplan_schema_dump.md` 로 저장해라 (PigOS 쪽에서 읽을 것).

---

### ★ 검증된 스키마 앵커 (선행 파악됨 — 가설로 삼고 라이브 DB로 재검증할 것)

> 아래는 피그플랜 애플리케이션 코드/이관 스크립트에서 도출한 실제 테이블·코드값이다. **추측이 아니라 코드 기준 확정치**지만, 컬럼 존재·타입은 반드시 `user_tab_columns`로 재확인해라. `FARM_NO`가 농장 식별키다(정수). 코드 컬럼명은 대부분 `*_CD`, `*_GUBUN_CD`.

**마스터**
| 테이블 | 의미 | 키/주요 컬럼 |
|---|---|---|
| `TA_FARM` | 농장 마스터 | PK `FARM_NO`. `FARM_NM, USE_YN, TEST_YN`('N'=실농장), `STOP_DT`(계약종료), `COMPANY_CD, SOLE_CD, AGENT_CD, PRINCIPAL_NM, BILL_DAY, FOUNDATION` |
| `TB_MODON` | 모돈 마스터 | (`FARM_NO,PIG_NO`). `FARM_PIG_NO, PUMJONG_CD, BIRTH_DT, IN_DT, IN_SANCHA, STATUS_CD, OUT_DT, OUT_GUBUN_CD, OUT_REASON_CD, SALE_COM_CD, BUY_COM_CD, USE_YN` |
| `TB_UNGDON` | 웅돈 마스터 | (`FARM_NO,PIG_NO`). `OUT_DT, OUT_GUBUN_CD, OUT_REASON_CD, SALE_COM_CD, SALE_PRICE, USE_YN` |

**번식 작업이력** (모돈 이벤트)
| 테이블 | 의미 |
|---|---|
| `TB_MODON_WK` | 모돈 작업 공통 이력. `WK_GUBUN` 로 종류 구분(B=분만, E=이유 등), `SANCHA`(산차), `DAERI_YN`(대리포유='Y'=유모), `WK_DT` |
| `TB_GYOBAE` | 교배 |
| `TB_BUNMAN` | 분만 |
| `TB_EU` | 이유 |
| `TB_SAGO` | 사고/재발정 |
| `TB_MODON_JADON_TRANS` | 모돈-자돈 양자 전출입(자돈 이동) |
| `TG_BUN_JADON` | 분만 자돈(포유자돈) |

**그룹/두수(자돈·비육), 거래처, 설정, 코드**
| 테이블 | 의미 |
|---|---|
| `TJ_GAIN_GRP` | 자돈/비육 그룹. (`FARM_NO,GRP_NO`). `GRP_ID, JU_GUBUN, ILRYUNG, SDATE, EDATE`(열림=9999-12-31), `LOC_CD, USE_YN` |
| `TJ_DUSU_MNG` | 그룹 두수 이력. `WK_DT, GUBUN_CD, SUB_GUBUN_CD, DUSU, DUSU_SU` |
| `TC_FARM_COMP` | 농장 거래처. (`FARM_NO,COMP_CD`). `COMP_GUBUN_CD, COMP_NM, USE_YN` |
| `TM_ETC_TRADE` | 기타거래/수익. `SEQ, WK_DT, COMP_CD, AUTO_GB, MP_PIG_NO, ACCOUNT_CD` |
| `TC_FARM_CONFIG` | 농장별 설정. (`FARM_NO,CODE,CVALUE,USE_YN`). 미설정 시 마스터값 상속 |
| `TC_CODE_SYS` | 공통코드 마스터. `PCODE,CODE,CNAME,CVALUE,CVALUE_2,LANGUAGE_CD('ko'),SORT_NO,USE_YN` |
| `TC_CODE_JOHAP` | 품종/사유 등 코드. `PCODE,CODE,CNAME,LANGUAGE_CD` |

**코드 사전(PCODE 기준 — 아래 두 테이블 덤프로 대부분 커버됨)**
- `TC_CODE_SYS` : PCODE `'01'`=모돈상태(STATUS_CD) · `'08'`=출하/도폐사구분(OUT_GUBUN_CD) · `'13'`=거래처구분 · `'14'`=농장환경설정 · `'16'`=포유작업(160003 재포유=양자전입 / 160004 양자전출)
- `TC_CODE_JOHAP` : PCODE `'041'`=품종(PUMJONG_CD) · `'031'`=도폐사/전출 사유(OUT_REASON_CD)
- `TJ_DUSU_MNG.GUBUN_CD` : `11`전입 · `12`전출(SUB `120001` 위탁 등) · `20`출하(SUB `200003` 자돈출하 등) · `033`폐사

---

### A. 번식 도메인 테이블 확정
위 앵커 테이블들이 실제 존재하는지 확인하고, 누락/추가 후보를 찾아라.
```sql
SELECT table_name, num_rows FROM user_tables ORDER BY num_rows DESC NULLS LAST;
```
```sql
SELECT table_name, comments FROM user_tab_comments WHERE comments IS NOT NULL ORDER BY table_name;
```
- 앵커에 없는데 `MODON/UNGDON/GYOBAE/BUNMAN/EU/SAGO/JADON/GAIN_GRP/FARM` 이름을 가진 테이블이 있으면 추가로 지목.
- 교배/이유가 `TB_MODON_WK` 하위인지 별도 상세 테이블(`TB_GYOBAE/TB_EU`)인지 **관계를 확인**해라.

### B. 각 핵심 테이블의 컬럼 상세
앵커 테이블 각각에 대해 컬럼명·타입·널여부·**컬럼 코멘트(한글 의미)** 덤프. (테이블명을 f-string으로 넣어 순회)
```sql
SELECT c.column_name, c.data_type, c.data_length, c.nullable, m.comments
FROM user_tab_columns c
LEFT JOIN user_col_comments m
  ON m.table_name = c.table_name AND m.column_name = c.column_name
WHERE c.table_name = 'TB_MODON'      -- ← 대상 테이블마다 교체
ORDER BY c.column_id;
```

### C. 샘플 로우
각 핵심 테이블에서 **정상 이력이 있는 최근 로우 5건** (실제 값 형태 파악용). 개인정보(농장주 이름/전화 등)는 마스킹 가능. 번식 데이터(날짜·두수·코드값)는 원본 그대로.
```sql
SELECT * FROM TB_MODON WHERE USE_YN='Y' AND ROWNUM <= 5 ORDER BY IN_DT DESC;  -- 예시
```

### D. 코드값 사전 (가장 중요)
**컬럼별 DISTINCT를 뒤지지 말고, 코드가 중앙화된 아래 두 테이블을 PCODE별로 통째 덤프**해라:
```sql
SELECT PCODE, CODE, CNAME, CVALUE, CVALUE_2, SORT_NO
FROM TC_CODE_SYS
WHERE LANGUAGE_CD='ko' AND USE_YN='Y'
ORDER BY PCODE, SORT_NO, CODE;
```
```sql
SELECT PCODE, CODE, CNAME
FROM TC_CODE_JOHAP
WHERE LANGUAGE_CD='ko'
ORDER BY PCODE, CODE;
```
그 후 아래 매핑을 표로 정리(위 앵커의 PCODE 힌트 참고): 모돈상태('01'), 출하/도폐사구분('08'), 사유(JOHAP '031'), 품종(JOHAP '041'), 포유/양자('16'), 거래처구분('13'), 농장설정('14'). 실제 데이터에 쓰인 코드만 교차확인하려면:
```sql
SELECT STATUS_CD, COUNT(*) FROM TB_MODON GROUP BY STATUS_CD ORDER BY 2 DESC;  -- 컬럼 교체하며 스팟체크
```

### E. 농장 식별 + 대상 농장 목록
- 농장 식별키 = **`FARM_NO`**(정수), 농장명 = `TA_FARM.FARM_NM`.
- 이관 대상 목록을 **`TA_FARM`에서 직접** 뽑되 **테스트 농장 제외**:
```sql
SELECT F.FARM_NO, F.FARM_NM, F.COMPANY_CD, F.STOP_DT,
       (SELECT COUNT(*) FROM TB_MODON M WHERE M.FARM_NO=F.FARM_NO AND M.USE_YN='Y') AS MODON_CNT,
       (SELECT MAX(WK_DT) FROM TB_MODON_WK W WHERE W.FARM_NO=F.FARM_NO) AS LAST_WK_DT
FROM TA_FARM F
WHERE F.USE_YN='Y' AND F.TEST_YN='N'
ORDER BY MODON_CNT DESC;
```

**★ 파일럿 대상(우선 검증) 4개 농장 = `FARM_NO IN (2807, 4448, 848, 978)`**
이 3개 농장에 대해 아래를 추가로 확인해 매핑 검증에 쓸 수 있는지 판단해라 (데이터 충실도 체크):
```sql
SELECT F.FARM_NO, F.FARM_NM,
       (SELECT COUNT(*) FROM TB_MODON     M WHERE M.FARM_NO=F.FARM_NO AND M.USE_YN='Y') AS 모돈수,
       (SELECT COUNT(*) FROM TB_MODON_WK  W WHERE W.FARM_NO=F.FARM_NO)                   AS 작업이력,
       (SELECT COUNT(*) FROM TB_BUNMAN    B WHERE B.FARM_NO=F.FARM_NO)                   AS 분만,
       (SELECT COUNT(*) FROM TB_GYOBAE    G WHERE G.FARM_NO=F.FARM_NO)                   AS 교배,
       (SELECT COUNT(*) FROM TB_EU        E WHERE E.FARM_NO=F.FARM_NO)                   AS 이유,
       (SELECT MIN(WK_DT) FROM TB_MODON_WK W WHERE W.FARM_NO=F.FARM_NO)                  AS 최초작업,
       (SELECT MAX(WK_DT) FROM TB_MODON_WK W WHERE W.FARM_NO=F.FARM_NO)                  AS 최근작업
FROM TA_FARM F
WHERE F.FARM_NO IN (2807, 4448, 848, 978);
```
- 샘플 로우(섹션 C)도 가급적 이 4개 농장에서 뽑아라(`WHERE FARM_NO IN (2807,4448,848,978)`).
- (국가 컬럼이 `TA_FARM`에 있으면 함께 표기.)

### F. 데이터 규모 요약
핵심 테이블별 전체 로우 수 + 날짜 범위(min/max)를 표로. `user_tables.num_rows`는 통계라 부정확할 수 있으니 **핵심 테이블은 `COUNT(*)`로 재확인**:
```sql
SELECT 'TB_MODON_WK' AS T, COUNT(*) CNT, MIN(WK_DT) MIN_DT, MAX(WK_DT) MAX_DT FROM TB_MODON_WK
UNION ALL SELECT 'TB_BUNMAN', COUNT(*), MIN(WK_DT), MAX(WK_DT) FROM TB_BUNMAN
-- … 핵심 테이블 반복
;
```

---

## 산출물
`c:/dev/PigOS/tests/db/pigplan_schema_dump.md` 하나에 A~F를 담아 저장. 표/코드블록으로 정리.
**데이터를 추출·이관하지 말 것. SELECT 조회·요약만.** 이번 단계는 스키마·코드값 파악이 전부다. 실제 추출 SQL은 이 덤프를 받은 PigOS 쪽에서 매핑 설계 후 2단계 프롬프트로 지시한다.
