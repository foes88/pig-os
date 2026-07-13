# PigPlan Oracle 스키마 덤프 (1단계 발견)

> 생성: 2026-07-10 10:42 · wiselake-console/oracle_connector.py (oracledb thin, 읽기전용) · 파일럿 농장 `2807,4448,848,978`

## A. 앵커 테이블 존재/규모


| table_name | num_rows |
| --- | --- |
| TA_FARM | 3201 |
| TB_BUNMAN | 11674153 |
| TB_EU | 11568214 |
| TB_GYOBAE | 15112123 |
| TB_MODON | 3349810 |
| TB_MODON_JADON_TRANS | 10222829 |
| TB_MODON_WK | 40851749 |
| TB_SAGO | 2750640 |
| TB_UNGDON | 59207 |
| TC_CODE_JOHAP | 2601 |
| TC_CODE_SYS | 2588 |
| TC_FARM_COMP | 17861 |
| TC_FARM_CONFIG | 603648 |
| TG_BUN_JADON | 4745810 |
| TJ_DUSU_MNG | 2531291 |
| TJ_GAIN_GRP | 150588 |
| TM_ETC_TRADE | 2227793 |


### 관련 테이블 코멘트


| table_name | comments |
| --- | --- |
| TA_ACCESS_REQUEST | 외부인 접근 신청/승인 이력 |
| TA_AMOUNT_SECTION | 서비스 구간별 요금 |
| TA_AUTHINFO | 권한정보 |
| TA_AUTHMENU_INFO | 권한별 메뉴정보 |
| TA_COMPANY | 업체 정보 |
| TA_COMPANY_AREA | 총판/특약점 정보 |
| TA_CONTRACK | 서비스 계약정보 |
| TA_ERROR_LOG | 시스템 에러 로그 |
| TA_FAQ | FAQ |
| TA_FARM | 농장정보 |
| TA_FARM_LEVEL | 농장등급설정 |
| TA_FARM_STATS_INFO | 현재 농가별 중요 통계지표 |
| TA_KAKAOMSG_SENT | 카카오/SMS발송 로그 |
| TA_LOGIN_LOG | 시스템 방문 로그 |
| TA_MEMBER | 회원정보 |
| TA_MEMBER_AUTH | 회원별 권한매핑 |
| TA_MEMBER_SYSSET | 회원별 환경정보 |
| TA_MENU | 메뉴정보 |
| TA_MENU_ITEM_INFO | 메뉴별 항목정보 |
| TA_MENU_LOGIN_LOG | 기능별 접속 로그 |
| TA_NOTIC | 공지사항 |
| TA_OTP_HISTORY | OTP 발송/검증 이력 |
| TA_QA | 헬프데스크 |
| TA_REPORT_BATCH | 보고서 일괄출력 |
| TA_REPORT_LOG | 보고서 출력 로그 |
| TA_REPORT_MRD | 보고서 파일 정보 |
| TA_REPORT_ONLY | 보고서 전용/미대상 여부 |
| TA_REPORT_PARAM | 리포트 파라미터 정보 |
| TA_SERVICECOUNTRY_INFO | 국가별서비스 세부정보 |
| TA_SERVICEINFO | 서비스 정보 |
| TA_SERVICEMENU | 서비스/메뉴 매칭 |
| TA_SERVICEMONTH_PAY_INFO | 서비스 월별 청구내역 |
| TA_SERVICE_HIS | 서비스 이용내역 |
| TA_SERVICE_USAGE_INFO | 청구/수금 내역 |
| TA_SYS_CONFIG | 시스템 설정 테이블 |
| TA_USERSERVICE_INFO | 이용 서비스 정보 |
| TA_USER_BOOKMARK | 북마크 |
| TA_USER_MENU | 회원별 맞춤 메뉴정보 |
| TA_USER_MENUITEM_INFO | 회원 메뉴별 항목정보 |
| TA_USER_SESSION | 사용자 세션 (admin/advisor/farm/external 통합) |
| TB_AIREST | 보존성 검사관리 |
| TB_BUNMAN | 분만정보 |
| TB_DILUTION | 희석제 제조관리 |
| TB_EU | 이유정보 |
| TB_FARM_WORKDAY_REPORT | 농장 작업일지 |
| TB_GYOBAE | 교배정보 |
| TB_MD_ESTRUS | 초발정정보 |
| TB_MD_LOC_TRANS | 모돈 장소이동 정보 |
| TB_MODON | 모돈정보 |
| TB_MODON_FARM_MOVE | 모/웅돈/검정 농장이동정보 |
| TB_MODON_GRP | 모돈그룹정보 |
| TB_MODON_GRP_DETAIL | 모돈그룹상세정보 |
| TB_MODON_JADON_TRANS | 포유자돈정보 |
| TB_MODON_WK | 모돈 작업정보 |
| TB_PIG_FEED | 사료급이정보 |
| TB_PIG_HEAL | 치료정보 |
| TB_PLAN_MODON | 모돈 예정작업정보 |
| TB_PLAN_UNGDON | 웅돈 예정작업정보 |
| TB_SAGO | 임신사고정보 |
| TB_SPERM | 정액 채취/제조관리 |
| TB_UNGDON | 웅돈정보 |
| TB_WT_BCS | 체중 등지방 정보 |
| TC_ACCOUNT | 계정코드정보 |
| TC_CODE_COMPANY | 업체코드정보 |
| TC_CODE_FARM | 농장코드정보 |
| TC_CODE_JOHAP | 공통코드정보_조합 |
| TC_CODE_SYS | 공통코드정보 |
| TC_DONSA | 돈사정보 |
| TC_ETC_UPLOAD_DAT | 업로드 데이터(번식돈) |
| TC_ETC_UPLOAD_DAT_ERR | 업로드 데이터 검증결과(번식돈) |
| TC_FARM_COMP | 농가 거래처정보 |
| TC_FARM_CONFIG | 농가설정정보 |
| TC_FARROWING | 분만틀정보 |
| TC_FILE_CREATE_HISTORY | 파일생성 이력관리 |
| TC_FILE_FIELD | 파일 항목관리 |
| TC_FILE_INFO | 파일 정보관리 |
| TC_FILE_SET | 파일 환경관리 |
| TC_FILE_UPLOAD_DAT | 업로드 데이터 |
| TC_FILE_UPLOAD_DAT_ERR | 업로드 데이터 검증결과 |
| TC_FILE_USER_FIELD | 사용자 파일 항목관리 |
| TC_I18N_MSG_M | 용어사전 |
| TC_I18N_MSG_SUB | 용어사전_다국어 |
| TC_JD_UPLOAD_DAT | 업로드 데이터(비육) |
| TC_JD_UPLOAD_DAT_ERR | 업로드 데이터 검증결과(비육) |
| TC_JONG_FARM | 종돈장 정보 |
| TC_LOC | 돈방정보 |
| TC_LOC_CON_VIN | 돈방 사료빈 정보 |
| TC_MDFILE_UPLOAD_DAT | 업로드 데이터(번식돈) |
| TC_MDFILE_UPLOAD_DAT_ERR | 업로드 데이터 검증결과(번식돈) |
| TC_MNGFILE_UPLOAD_DAT | 업로드 데이터(경영) |
| TC_MNGFILE_UPLOAD_DAT_ERR | 업로드 데이터 검증결과(경영) |
| TC_SERVICE | 공통 인증 서비스를 이용하는 시스템 마스터 |
| TC_STD_GAIN | 사료지표정보 |
| TC_STD_GAIN_CJ | 사료지표정보 |
| TC_USER_CONFIG | 산차설정정보 |
| TC_VIN | 사료빈 정보 |
| TG_BUN_JADON | 검정돈 정보 |
| TG_BUN_JADON_RAISE | 검정돈 육종가 정보 |
| TJ_BATCH_DUSU_MNG | 일괄두수이동정보 |
| TJ_DUSU_MNG | 비육돈그룹두수이동정보 |
| TJ_GAIN_GRP | 비육돈그룹정보 |
| TJ_GAIN_GRP_HEAL | 비육돈그룹치료정보 |
| TJ_GRP_LOC_TRANS | 비육돈그룹장소이동정보 |
| TJ_PLAN_GAIN | 비돈 예정작업정보 |


## B. 핵심 테이블 컬럼 상세

### TA_FARM


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | N | 농장번호 |
| FARM_NM | VARCHAR2 | 100 | Y | 농가명 |
| PRINCIPAL_NM | VARCHAR2 | 50 | Y | 대표자명 |
| ADM_CD | VARCHAR2 | 200 | Y | 행정구역코드 |
| SIDO_CD | VARCHAR2 | 20 | Y | 시도코드 |
| SIGUN_CD | VARCHAR2 | 20 | Y | 시군코드 |
| ZIPCODE | VARCHAR2 | 20 | Y | 우편번호 |
| RNMGTSN | VARCHAR2 | 20 | Y | 도로명코드 |
| EMDNO | VARCHAR2 | 20 | Y | 읍면동 일련번호 |
| ADDR1 | VARCHAR2 | 200 | Y | 주소 |
| ADDR2 | VARCHAR2 | 200 | Y | 상세주소 |
| MAP_X | NUMBER | 22 | Y | 상세 경도 (WGS84, 고정밀) |
| MAP_Y | NUMBER | 22 | Y | 상세 위도 (WGS84, 고정밀) |
| OFFICE_TEL | VARCHAR2 | 20 | Y | 사무실 전화번호 |
| FAX | VARCHAR2 | 20 | Y | 팩스번호 |
| FOUNDATION | VARCHAR2 | 13 | Y | 사업자번호 |
| FARM_TYPE | VARCHAR2 | 6 | Y | 농가구분 |
| CREATE_DT | DATE | 7 | Y | 전산가입일 |
| ICT_YN | CHAR | 1 | Y | ICT장비 연계여부 |
| EKAPE_NO | VARCHAR2 | 20 | Y | 축평원 연계번호 |
| COMPANY_CD | NUMBER | 22 | Y | 업체코드 |
| SOLE_CD | NUMBER | 22 | Y | 총판코드 |
| AGENT_CD | NUMBER | 22 | Y | 특약점코드 |
| JONG_CD | NUMBER | 22 | Y | 종돈장코드 |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| ETC_FEED_CD | VARCHAR2 | 6 | Y |  비율구분코드(스마트팜) |
| FEED_RATIO | NUMBER | 22 | Y |  경영비중 사료비비율(스마트팜) |
| COUNTRY_CODE | VARCHAR2 | 6 | Y | 국가코드 |
| MONEY_SIGN | VARCHAR2 | 5 | Y | 통화기호 |
| MONEY_1000SING | CHAR | 1 | Y | 통화천단위기호 |
| MONEY_DECIMALPOINT | NUMBER | 22 | Y | 통화소수점자릿수 |
| MONEY_DECIMALSING | CHAR | 1 | Y | 통화소숫점기호 |
| MONEY_ALIGN | VARCHAR2 | 10 | Y | 통화정렬 |
| CONTRACK_TARGET | VARCHAR2 | 6 | Y | 계약 주체(934) |
| CONTRACK_NO | VARCHAR2 | 30 | Y | 계약번호 |
| COMP_ACRONYM | VARCHAR2 | 4 | Y | 농가/거래처 약어코드(cj용) |
| CJ_CD | VARCHAR2 | 20 | Y | CJ 농장코드 |
| CI_PATH | VARCHAR2 | 1000 | Y | CI 경로 |
| FARM_ACRONYM_01 | VARCHAR2 | 10 | Y | 농가 약어코드 - 다비육종(다른 업체도 공용 사용 가능) |
| KD_FILE_DOWNGB | VARCHAR2 | 6 | Y | 검정파일다운대상구분(산육번식,등기출력 등 다운로드 대상농가) |
| RD_CI_PATH | VARCHAR2 | 200 | Y | nan |
| GRP_CD | VARCHAR2 | 6 | Y | 그룹코드 |
| ALIAS_FARM_NM | VARCHAR2 | 200 | Y | 별칭 농가명(다비에서 사용) |
| STOP_DT | DATE | 7 | Y | 종단일자 |
| RESTART_DT | DATE | 7 | Y | 재 시작일자 |
| FOUNDATION_PATH | VARCHAR2 | 1000 | Y | 사업자등록증 경로 |
| FOUNDATION_NM | VARCHAR2 | 200 | Y | 사업자등록증 파일명 |
| TEST_YN | VARCHAR2 | 1 | Y | 테스트 여부(농가) |
| BILL_DAY | NUMBER | 22 | Y | 정산 기준일 |
| INFO_JSON | CLOB | 4000 | Y | 추가설정정보(JSON) |
| MANAGER_INFO | VARCHAR2 | 4000 | Y | 담당자 정보 |
| WEATHER_NX | NUMBER | 22 | Y | 기상청 격자 X좌표-삭제예정 |
| WEATHER_NY | NUMBER | 22 | Y | 기상청 격자 Y좌표-삭제예정 |
| MAP_X_N | NUMBER | 22 | Y | 대표 경도 (WGS84, 고정밀) |
| MAP_Y_N | NUMBER | 22 | Y | 대표 위도 (WGS84, 고정밀) |
| WEATHER_NX_N | NUMBER | 22 | Y | 기상청 격자 X좌표 (5km 단위, MAP_X_N로부터 변환) |
| WEATHER_NY_N | NUMBER | 22 | Y | 기상청 격자 Y좌표 (5km 단위, MAP_Y_N로부터 변환) |
| ASOS_STN_ID | NUMBER | 22 | Y | ASOS 관측소 지점번호 (TM_WEATHER_ASOS.STN_ID) |
| ASOS_STN_NM | VARCHAR2 | 50 | Y | ASOS 관측소명 (조회 편의용) |
| ASOS_DIST_KM | NUMBER | 22 | Y | 농장에서 관측소까지 거리 (km) |


### TB_MODON


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | Y | 농장번호 |
| PIG_NO | NUMBER | 22 | Y | 시스템번호 |
| FARM_PIG_NO | VARCHAR2 | 40 | Y | 개체번호 |
| PUMJONG_CD | VARCHAR2 | 6 | Y | 품종코드 |
| IGAK_NO | VARCHAR2 | 40 | Y | 이각번호 |
| BIRTH_DT | DATE | 7 | Y | 출생일 |
| IN_DT | DATE | 7 | Y | 전입일 |
| IN_SANCHA | NUMBER | 22 | N | 전입산차 |
| IN_GYOBAE_CNT | NUMBER | 22 | N | 전입교배차수 |
| IN_KG | NUMBER | 22 | Y | 전입체중 |
| STATUS_CD | VARCHAR2 | 6 | N | 전입상태 |
| LAST_WK_DT | DATE | 7 | Y | 최종작업일 |
| HYULTONG_NO | VARCHAR2 | 40 | Y | 혈통번호 |
| MO_PIG_NO | VARCHAR2 | 40 | Y | 모돈 개체번호 |
| UN_PIG_NO | VARCHAR2 | 40 | Y | 부돈 개체번호 |
| MO_HYUL_NO | VARCHAR2 | 40 | Y | 모돈 혈통번호 |
| UN_HYUL_NO | VARCHAR2 | 40 | Y | 부돈 혈통번호 |
| OUT_DT | DATE | 7 | Y | 도폐사일 |
| OUT_GUBUN_CD | VARCHAR2 | 6 | Y | 도폐사 구분코드 |
| OUT_REASON_CD | VARCHAR2 | 6 | Y | 도폐사 원인코드 |
| OUT_REASON_DETAIL | VARCHAR2 | 2000 | Y | 도폐사 사유 |
| OUT_KG | NUMBER | 22 | Y | 판매체중 |
| RFID_NO | VARCHAR2 | 50 | Y | 전자이표번호 |
| PSS | CHAR | 1 | Y | PSS |
| FAMILY_CD | VARCHAR2 | 6 | Y | 가계코드 |
| BIGO | VARCHAR2 | 200 | Y | 비고 |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| SALE_PRICE | NUMBER | 22 | Y | nan |
| IN_LOC_CD | NUMBER | 22 | Y | 전입장소 |
| BUY_COM_CD | NUMBER | 22 | Y | nan |
| MOVE_IN_GUBUN | VARCHAR2 | 2 | Y | 전입구분-CJ용 |
| MOVE_FARM_NO | NUMBER | 22 | Y | 전입출 농가코드 |
| MOVE_OUT_PIG_NO | NUMBER | 22 | Y | 전출 모돈번호 |
| MOBILE | VARCHAR2 | 1 | Y | 모바일 |
| MOBILE_DIE | VARCHAR2 | 1 | Y | 모바일(도폐사용) |
| LOG_UPT_ID_DIE | VARCHAR2 | 40 | Y | 수정자(도폐사용) |
| LOG_UPT_DT_DIE | DATE | 7 | Y | 수정리(도폐사용) |
| EKAPE_SOW_NO | VARCHAR2 | 12 | Y | 축평원 모돈번호 |
| SALE_COM_CD | NUMBER | 22 | Y | nan |


### TB_UNGDON


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | Y | 농장번호 |
| PIG_NO | NUMBER | 22 | Y | 시스템번호 |
| FARM_PIG_NO | VARCHAR2 | 40 | Y | 개체번호 |
| IGAK_NO | VARCHAR2 | 40 | Y | 이각번호 |
| BIRTH_DT | DATE | 7 | Y | 출생일 |
| IN_DT | DATE | 7 | Y | 전입일 |
| JASAN_DT | DATE | 7 | Y | 종모편입일 |
| PUMJONG_CD | VARCHAR2 | 6 | Y | 품종코드 |
| GUBUN_CD | VARCHAR2 | 6 | Y | 구분코드 |
| IN_KG | NUMBER | 22 | Y | 전입체중 |
| HYULTONG_NO | VARCHAR2 | 20 | Y | 혈통번호 |
| MO_PIG_NO | VARCHAR2 | 40 | Y | 모돈 개체번호 |
| UN_PIG_NO | VARCHAR2 | 40 | Y | 부돈 개체번호 |
| MO_HYUL_NO | VARCHAR2 | 40 | Y | 모돈 혈통번호 |
| UN_HYUL_NO | VARCHAR2 | 40 | Y | 부돈 혈통번호 |
| OUT_DT | DATE | 7 | Y | 도폐사일 |
| OUT_GUBUN_CD | VARCHAR2 | 6 | Y | 도폐사 구분코드 |
| OUT_REASON_CD | VARCHAR2 | 6 | Y | 도폐사 원인코드 |
| OUT_REASON_DETAIL | VARCHAR2 | 2000 | Y | 도폐사 사유 |
| OUT_KG | NUMBER | 22 | Y | 판매체중 |
| SALE_PRICE | NUMBER | 22 | Y | 판매금액 |
| RFID_NO | VARCHAR2 | 50 | Y | 전자이표번호 |
| PSS | CHAR | 1 | Y | PSS |
| FAMILY_CD | VARCHAR2 | 6 | Y | 가계코드 |
| BIGO | VARCHAR2 | 2000 | Y | 비고 |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| BUY_COM_CD | NUMBER | 22 | Y | nan |
| MOVE_IN_GUBUN | VARCHAR2 | 2 | Y | 전입구분-CJ용 |
| MOVE_FARM_NO | NUMBER | 22 | Y | 전입출 농가코드 |
| MOVE_OUT_PIG_NO | NUMBER | 22 | Y | 전출 모돈번호 |
| MOBILE | VARCHAR2 | 1 | Y | 모바일 |
| MOBILE_DIE | VARCHAR2 | 1 | Y | 모바일(도폐사용) |
| LOG_UPT_ID_DIE | VARCHAR2 | 40 | Y | 수정자(도폐사용) |
| LOG_UPT_DT_DIE | DATE | 7 | Y | 수정리(도폐사용) |
| SALE_COM_CD | NUMBER | 22 | Y | nan |


### TB_MODON_WK


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | N | 농장번호 |
| PIG_NO | NUMBER | 22 | N | 시스템번호 |
| WK_DT | CHAR | 8 | N | 작업일자 |
| WK_GUBUN | CHAR | 1 | N | 작업구분 |
| WK_DATE | DATE | 7 | Y | 작업일 |
| SANCHA | NUMBER | 22 | N | 산차 |
| GYOBAE_CNT | NUMBER | 22 | N | 교배차수 |
| LOC_CD | NUMBER | 22 | Y | 돈방코드 |
| SAGO_GUBUN_CD | VARCHAR2 | 6 | Y | 임신사고 구분코드 |
| DAERI_YN | CHAR | 1 | Y | 대리모여부 |
| SEQ | NUMBER | 22 | Y | 일련번호 |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| AUTO_GB | VARCHAR2 | 1 | Y | 자동생성 구분 : A(전입), Z(도폐사) |
| FW_NO | NUMBER | 22 | Y | 분만틀번호 |
| MOBILE | VARCHAR2 | 1 | Y | 모바일 |
| EKAPE_IUFLAG | VARCHAR2 | 1 | Y | 축평원(C:등록,U:수정,D:삭제) |
| EKAPE_WK_DT | VARCHAR2 | 8 | Y | 축평원 전송작업일자 |


### TB_GYOBAE


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | N | 농장번호 |
| PIG_NO | NUMBER | 22 | N | 시스템번호 |
| WK_DT | CHAR | 8 | N | 작업일자 |
| WK_GUBUN | CHAR | 1 | N | 작업구분 |
| METHOD_1 | CHAR | 1 | N | 웅돈1회 교배방법 |
| METHOD_2 | CHAR | 1 | Y | 웅돈2회 교배방법 |
| METHOD_3 | CHAR | 1 | Y | 웅돈3회 교배방법 |
| UNGDON_PIG_NO_1 | NUMBER | 22 | Y | 웅돈1회 시스템번호 |
| UNGDON_PIG_NO_2 | NUMBER | 22 | Y | 웅돈2회 시스템번호 |
| UNGDON_PIG_NO_3 | NUMBER | 22 | Y | 웅돈3회 시스템번호 |
| UFARM_PIG_NO_1 | VARCHAR2 | 40 | Y | 웅돈1회 개체번호 |
| UFARM_PIG_NO_2 | VARCHAR2 | 40 | Y | 웅돈2회 개체번호 |
| UFARM_PIG_NO_3 | VARCHAR2 | 40 | Y | 웅돈3회 개체번호 |
| WK_PERSON_CD | VARCHAR2 | 4 | Y | 작업자 |
| BIGO | VARCHAR2 | 200 | Y | 비고 |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| MOBILE | VARCHAR2 | 1 | Y | 모바일 |


### TB_BUNMAN


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | N | 농장번호 |
| PIG_NO | NUMBER | 22 | N | 시스템번호 |
| WK_DT | CHAR | 8 | N | 작업일자 |
| WK_GUBUN | CHAR | 1 | N | 작업구분 |
| SILSAN | NUMBER | 22 | Y | 실산 |
| MILA | NUMBER | 22 | Y | 미라 |
| SASAN | NUMBER | 22 | Y | 사산 |
| BUNMAN_GUBUN_CD | VARCHAR2 | 6 | Y | 분만구분코드 |
| SAENGSI_KG | NUMBER | 22 | Y | 생시체중 |
| SILSAN_AM | NUMBER | 22 | Y | 실산(암) |
| SILSAN_SU | NUMBER | 22 | Y | 실산(수) |
| BIGO | VARCHAR2 | 2000 | Y | 비고 |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| JD_IGAK_NO | VARCHAR2 | 100 | Y | 자돈이각번호(PIC용) |
| MOBILE | VARCHAR2 | 1 | Y | 모바일 |


### TB_EU


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | N | 농장번호 |
| PIG_NO | NUMBER | 22 | N | 시스템번호 |
| WK_DT | CHAR | 8 | N | 작업일자 |
| WK_GUBUN | CHAR | 1 | N | 작업구분 |
| DUSU | NUMBER | 22 | Y | 두수(암) |
| DUSU_SU | NUMBER | 22 | Y | 두수(수) |
| ILRYUNG | NUMBER | 22 | Y | 일령 |
| TOTAL_KG | NUMBER | 22 | Y | 총체중 |
| DAERI_YN | CHAR | 1 | Y | 대리모여부 |
| BIGO | VARCHAR2 | 200 | Y | 비고 |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| MOBILE | VARCHAR2 | 1 | Y | 모바일 |


### TB_SAGO


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | N | 농장번호 |
| PIG_NO | NUMBER | 22 | N | 시스템번호 |
| WK_DT | CHAR | 8 | N | 작업일자 |
| WK_GUBUN | CHAR | 1 | N | 작업구분 |
| SAGO_GUBUN_CD | VARCHAR2 | 6 | Y | 임신사고 구분코드 |
| BIGO | VARCHAR2 | 200 | Y | 비고 |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| MOBILE | VARCHAR2 | 1 | Y | 모바일 |


### TB_MODON_JADON_TRANS


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | Y | 농장번호 |
| PIG_NO | NUMBER | 22 | Y | 시스템번호 |
| SEQ | NUMBER | 22 | Y | 일련번호 |
| SANCHA | NUMBER | 22 | Y | 산차 |
| GUBUN_CD | VARCHAR2 | 6 | Y | 구분코드 |
| SUB_GUBUN_CD | VARCHAR2 | 6 | Y | 상세작업구분코드 |
| WK_DT | DATE | 7 | Y | 작업일자 |
| DUSU | NUMBER | 22 | Y | 두수(암) |
| DUSU_SU | NUMBER | 22 | Y | 두수(수) |
| ILRYUNG | NUMBER | 22 | Y | 일령 |
| TOTAL_KG | NUMBER | 22 | Y | 총체중 |
| BUN_DT | DATE | 7 | Y | 분만일 |
| EU_DT | DATE | 7 | Y | 이유일 |
| IO_PIG_NO | NUMBER | 22 | Y | 보내거나 받은 모돈 시스템번호 |
| LOC_CD | NUMBER | 22 | Y | 돈방코드 |
| FW_NO | NUMBER | 22 | Y | 분만틀번호 |
| BIGO | VARCHAR2 | 200 | Y | 비고 |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| AUTO_GB | VARCHAR2 | 1 | Y | 자동생성 구분 : A(전입), Z(도폐사) |
| IO_SEQ | NUMBER | 22 | Y | 전입출 SEQ |
| MOBILE | VARCHAR2 | 1 | Y | nan |


### TG_BUN_JADON


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | Y | 농장번호 |
| JADON_PIG_NO | NUMBER | 22 | Y | 검정돈 시스템번호 |
| INSIK_NO | VARCHAR2 | 40 | Y | 검정돈 개체번호 |
| BIRTH_DT | DATE | 7 | Y | 출생일 |
| SEX | CHAR | 1 | Y | 성별 |
| PUMJONG_CD | VARCHAR2 | 6 | Y | 품종코드 |
| SAENGSI_KG | NUMBER | 22 | Y | 생시체중 |
| SANCHA | NUMBER | 22 | Y | 산차 |
| HYULTONG_NO | VARCHAR2 | 20 | Y | 혈통번호 |
| DUNG_PRINT_YN | CHAR | 1 | Y | 등기출력여부 |
| HYULTONG_IN_YN | CHAR | 1 | Y | 혈통번호 업데이트 여부 |
| TEAT_LEFT | NUMBER | 22 | Y | 유두(좌) |
| TEAT_RIGHT | NUMBER | 22 | Y | 유두(우) |
| RFID_NO | VARCHAR2 | 50 | Y | 전자이표번호 |
| MP_PIG_NO | NUMBER | 22 | Y | 모돈 시스템번호 |
| MO_PIG_NO | VARCHAR2 | 40 | Y | 모돈 개체번호 |
| UN_PIG_NO | VARCHAR2 | 40 | Y | 부돈 개체번호 |
| MO_HYUL_NO | VARCHAR2 | 20 | Y | 모돈 혈통번호 |
| UN_HYUL_NO | VARCHAR2 | 20 | Y | 부돈 혈통번호 |
| FAMILY_CD | VARCHAR2 | 6 | Y | 가계코드 |
| OUT_DT | DATE | 7 | Y | 도폐사일 |
| OUT_GUBUN_CD | VARCHAR2 | 6 | Y | 도폐사 구분코드 |
| EWK_DT | DATE | 7 | Y | 검정종료일 |
| ROOM_NO | VARCHAR2 | 20 | Y | 호실 |
| CHAMBER_NO | VARCHAR2 | 20 | Y | 돈방 |
| END_KG | NUMBER | 22 | Y | 종료체중 |
| PIG_LENGTH | NUMBER | 22 | Y | 체장 |
| PIG_HEIGHT | NUMBER | 22 | Y | 체고 |
| TEAT1 | NUMBER | 22 | Y | 재측정 유두(좌) |
| TEAT2 | NUMBER | 22 | Y | 재측정 유두(우) |
| TEAT3 | NUMBER | 22 | Y | 부/맹 |
| BACK_DEPTS | NUMBER | 22 | Y | 등심(피클) , 등심깊이(CJ) |
| BODY_PATT | NUMBER | 22 | Y | 체형-피클, 체폭-CJ |
| LEG_PATT | NUMBER | 22 | Y | 지제 |
| VULVA | NUMBER | 22 | Y | 외음부 |
| TEAT_PATT | NUMBER | 22 | Y | 유두형태 |
| FAT1 | NUMBER | 22 | Y | 등지방1 |
| FAT2 | NUMBER | 22 | Y | 등지방2 |
| FAT3 | NUMBER | 22 | Y | 등지방3 |
| DAY_KG | NUMBER | 22 | Y | 일별 증체량-자동계산 |
| FEED_EFF | NUMBER | 22 | Y | 사료요구율 |
| KG90 | NUMBER | 22 | Y | 90kg 도달일령-자동계산 |
| WEEK | CHAR | 6 | Y | 주차 |
| PREP1 | VARCHAR2 | 200 | Y | 기타항목1 |
| PREP2 | VARCHAR2 | 200 | Y | 기타항목2 |
| PREP3 | VARCHAR2 | 200 | Y | 기타항목3 |
| PREP4 | VARCHAR2 | 200 | Y | 기타항목4 |
| PREP5 | VARCHAR2 | 50 | Y | 기타항목5 |
| EDAYS | NUMBER | 22 | Y | 종료기간 |
| REFAT | NUMBER | 22 | Y | 보정등지방(표현)-자동계산 |
| TOTAL_OPI | VARCHAR2 | 500 | Y | 종합평가 |
| DRESSED | NUMBER | 22 | Y | 정육률 |
| MS | NUMBER | 22 | Y | 마블링스코어 |
| SELECT_DT | DATE | 7 | Y | 선발일 |
| SELECT_CD | VARCHAR2 | 6 | Y | 선발코드 |
| UNGDON_IDX | NUMBER | 22 | Y | 표현형가(웅돈) |
| MODON_IDX | NUMBER | 22 | Y | 표현형가(모돈) |
| INCES_IDX | NUMBER | 22 | Y | 표현형가(인덱스) |
| BR_DAY_KG | NUMBER | 22 | Y | 표현형가(증체중) |
| BR_FAT | NUMBER | 22 | Y | 표현형가(등지방) |
| BR_FEED | NUMBER | 22 | Y | 표현형가(사료) |
| BR_KG90 | NUMBER | 22 | Y | 표현형가(90kg도달) |
| BR_TPIG | NUMBER | 22 | Y | 표현형가(총산) |
| BR_RPIG | NUMBER | 22 | Y | 표현형가(RPIG) |
| BR_RETURN | NUMBER | 22 | Y | 표현형가(재귀) |
| BR_DEPTS | NUMBER | 22 | Y | 표현형가(등심) |
| BR_DRES | NUMBER | 22 | Y | 표현형가(정육) |
| GENE_PSS | CHAR | 3 | Y | 표현형가(PSS) |
| GENE_F18 | CHAR | 3 | Y | 표현형가(F18) |
| GENE_ESR | CHAR | 3 | Y | 표현형가(ESR) |
| USE_F | VARCHAR2 | 10 | Y | USE_F |
| ESR | NUMBER | 22 | Y | ESR |
| FABP1 | NUMBER | 22 | Y | FABP1 |
| IGF2 | NUMBER | 22 | Y | nan |
| PRK3 | NUMBER | 22 | Y | PRK3 |
| F4 | NUMBER | 22 | Y | F4 |
| MC4R | NUMBER | 22 | Y | MC4R |
| BR_KG90_G | NUMBER | 22 | Y | 육종가(90kg도달) |
| BR_TPIG_G | NUMBER | 22 | Y | 육종가(총산) |
| BR_RETURN_G | NUMBER | 22 | Y | 육종가(재귀) |
| BR_FEED_G | NUMBER | 22 | Y | 육종가(사료) |
| UNGDON_IDX_G | NUMBER | 22 | Y | 육종가(웅돈) |
| MODON_IDX_G | NUMBER | 22 | Y | 육종가(모돈) |
| USE_G | VARCHAR2 | 10 | Y | 육종가(USE) |
| BR_FAT_H | NUMBER | 22 | Y | 정확도(등지방) |
| BR_KG90_H | NUMBER | 22 | Y | 정확도(90kg도달) |
| BR_TPIG_H | NUMBER | 22 | Y | 정확도(총산) |
| BR_RETURN_H | NUMBER | 22 | Y | 정확도(재귀) |
| BR_FEED_H | NUMBER | 22 | Y | 정확도(사료) |
| BR_EU_H | NUMBER | 22 | Y | 정확도(이유) |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| OUT_BIGO | VARCHAR2 | 1000 | Y | 폐사비고 |
| UPIG_NO | NUMBER | 22 | Y | 웅돈시스템코드 |
| MOVE_FARM_NO | NUMBER | 22 | Y | 전/입출 농장코드 |
| MOVE_DT | DATE | 7 | Y | 이동일자 |
| SWK_DT | DATE | 7 | Y | 검정시작일 |
| PIG_LENGTH2 | NUMBER | 22 | Y | 체장2-CJ |
| BACK_CROSS_AREA | NUMBER | 22 | Y | 등심단면적-자동계산-CJ |
| START_KG | NUMBER | 22 | Y | 시작체중-CJ |
| USER_OK_CD | VARCHAR2 | 6 | Y | 승인/반려코드  - CJ |
| MV_BIGO | VARCHAR2 | 1000 | Y | 이동-비고 - CJ |
| LAST_WK_DT | DATE | 7 | Y | 최종작업일-CJ |
| LOG_UPT_DT_DIE | DATE | 7 | Y | 수정일자(폐사) |
| LOG_UPT_ID_DIE | VARCHAR2 | 40 | Y | 수정자(폐사) |
| LOG_UPT_DT_END | DATE | 7 | Y | 수정일자(종료) |
| LOG_UPT_ID_END | VARCHAR2 | 40 | Y | 수정자(종료) |
| LOG_UPT_DT_SEL | DATE | 7 | Y | 수정일자(선발) |
| LOG_UPT_ID_SEL | VARCHAR2 | 40 | Y | 수정자(선발) |
| LOG_UPT_DT_MV | DATE | 7 | Y | 수정일자(전입) |
| LOG_UPT_ID_MV | VARCHAR2 | 40 | Y | 수정자(전입) |
| LOG_UPT_DT_HT | DATE | 7 | Y | 수정일자(혈통병합) |
| LOG_UPT_ID_HT | VARCHAR2 | 40 | Y | 수정자(혈통병합) |
| BACK_AREA | NUMBER | 22 | Y | 등심면적:자동계산으로 입력 - CJ |
| MOVEIN_PIG_NO | NUMBER | 22 | Y | 이동-대상모돈 - CJ |
| JD_BIGO | VARCHAR2 | 4000 | Y | 비고(자돈생성) |


### TJ_GAIN_GRP


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | Y | 농장번호 |
| GRP_NO | NUMBER | 22 | Y | 그룹번호 |
| JU_GUBUN | CHAR | 1 | Y | 비육돈구분 |
| GRP_ID | VARCHAR2 | 100 | Y | 그룹명 |
| AUTO_YN | CHAR | 1 | Y | 자동생성여부(GP:그룹생성시 생성) |
| PUMJONG_CD | VARCHAR2 | 6 | Y | 품종코드 |
| ILRYUNG | NUMBER | 22 | Y | 일령 |
| SDATE | DATE | 7 | Y | 시작일 |
| EDATE | DATE | 7 | Y | 종료일 |
| BIGO | VARCHAR2 | 200 | Y | 비고 |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| LOC_CD | NUMBER | 22 | Y | 돈방 장소코드 |
| LOC_CJ_SEQ | NUMBER | 22 | Y | CJ : 돈방_순번 , 피클 : 돈방기준 관리시 돈방and생성일 순번 |
| MOBILE | VARCHAR2 | 1 | Y | nan |
| BIGO_END | VARCHAR2 | 4000 | Y | nan |
| MOBILE_END | VARCHAR2 | 1 | Y | nan |
| SEX | VARCHAR2 | 6 | Y | nan |


### TJ_DUSU_MNG


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | Y | 농장번호 |
| GRP_NO | NUMBER | 22 | Y | 그룹번호 |
| SEQ | NUMBER | 22 | Y | 일련번호 |
| JU_GUBUN | CHAR | 1 | Y | nan |
| WK_DT | DATE | 7 | Y | 작업일자 |
| GUBUN_CD | VARCHAR2 | 6 | Y | 구분코드 |
| SUB_GUBUN_CD | VARCHAR2 | 6 | Y | 상세작업구분코드 |
| DUSU | NUMBER | 22 | Y | 두수(암) |
| DUSU_SU | NUMBER | 22 | Y | 두수(수) |
| TOTAL_KG | NUMBER | 22 | Y | 지육체중(도체중) |
| NET_KG | NUMBER | 22 | Y | 출하체중 |
| TOTAL_PRICE | NUMBER | 22 | Y | 총금액 |
| PIG_NO | NUMBER | 22 | Y | 시스템번호 |
| BIGO | VARCHAR2 | 200 | Y | 비고 |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| DUSU1 | NUMBER | 22 | Y | 1등급 두수(암) |
| DUSU_SU1 | NUMBER | 22 | Y | 1등급 두수(수) |
| DUSU2 | NUMBER | 22 | Y | 2등급 두수(암) |
| DUSU_SU2 | NUMBER | 22 | Y | 2등급 두수(수) |
| DUSU3 | NUMBER | 22 | Y | 3등급 두수(암) |
| DUSU_SU3 | NUMBER | 22 | Y | 3등급 두수(수) |
| DUSU4 | NUMBER | 22 | Y | 4등급 두수(암) |
| DUSU_SU4 | NUMBER | 22 | Y | 4등급 두수(수) |
| DUSU5 | NUMBER | 22 | Y | 5등급 두수(암) |
| DUSU_SU5 | NUMBER | 22 | Y | 5등급 두수(수) |
| DUSU6 | NUMBER | 22 | Y | 6등급 두수(암) |
| DUSU_SU6 | NUMBER | 22 | Y | 6등급 두수(수) |
| DUSU7 | NUMBER | 22 | Y | 7등급 두수(암) |
| DUSU_SU7 | NUMBER | 22 | Y | 7등급 두수(수) |
| MOVE_GRP_NO | NUMBER | 22 | Y | 전출 그룹번호 |
| MOVE_FARM_NO | NUMBER | 22 | Y | 전출 농가코드 |
| MOVE_GRP_SEQ | NUMBER | 22 | Y | 전출그룹 일련번호 |
| EU_SEQ | NUMBER | 22 | Y | nan |
| ILRYUNG | NUMBER | 22 | Y | 일령 |
| BATCH_SEQ | NUMBER | 22 | Y | 배치순번 |
| MOBILE | VARCHAR2 | 1 | Y | nan |
| OUT_COM_CD | NUMBER | 22 | Y | nan |


### TC_FARM_COMP


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | Y | 농장번호 |
| COMP_GUBUN_CD | VARCHAR2 | 6 | Y | 거래처구분코드 |
| COMP_NM | VARCHAR2 | 100 | Y | 거래처명 |
| COMP_DESC | VARCHAR2 | 100 | Y | 거래처 설명 |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| COMP_ACRONYM | VARCHAR2 | 4 | Y | 거래처 코드약어 |
| COMP_CD | NUMBER | 22 | Y | 거래처코드 |
| CJ_CD | VARCHAR2 | 20 | Y | CJ전용 농가코드 |


### TC_FARM_CONFIG


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | Y | 농장번호 |
| CODE | VARCHAR2 | 6 | Y | 코드번호 |
| CVALUE | VARCHAR2 | 4000 | Y | 코드값 |
| DISPLAY_TYPE | VARCHAR2 | 50 | Y | 출력구분 |
| SORT_NO | NUMBER | 22 | Y | 정렬순번 |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| CVALUE_2 | VARCHAR2 | 200 | Y | nan |


### TM_ETC_TRADE


| column_name | data_type | data_length | nullable | comments |
| --- | --- | --- | --- | --- |
| FARM_NO | NUMBER | 22 | Y | 농장번호 |
| SEQ | NUMBER | 22 | Y | 일련번호 |
| WK_DT | DATE | 7 | Y | 작업일자 |
| ACCOUNT_CD | VARCHAR2 | 6 | Y | 계정코드 |
| SUB_GUBUN_CD | VARCHAR2 | 6 | Y | 상세작업구분코드 |
| FPER_PRICE | NUMBER | 22 | Y | 단가 |
| TOTAL_PRICE | NUMBER | 22 | Y | 총금액 |
| PRICE_CASH | NUMBER | 22 | Y | 현금 |
| PRICE_NCASH | NUMBER | 22 | Y | 외상 |
| UNIT | NUMBER | 22 | Y | 단위 |
| NET_KG | NUMBER | 22 | Y | 지육체중(도체중) |
| TOTAL_KG | NUMBER | 22 | Y | 총체중 |
| GRP_NO | NUMBER | 22 | Y | 그룹번호 |
| CK_USE_GUBUN_CD | VARCHAR2 | 6 | Y | 사료구분코드 |
| VIN_CD | VARCHAR2 | 6 | Y | 빈코드 |
| DRUG_SEQ | NUMBER | 22 | Y | nan |
| BUTCHERY_DT | DATE | 7 | Y | 도축일자 |
| VALIDITY_DT | DATE | 7 | Y | 유효기간 |
| BIGO | VARCHAR2 | 200 | Y | 비고 |
| USE_YN | CHAR | 1 | Y | 사용여부 |
| LOG_INS_DT | DATE | 7 | Y | 생성일 |
| LOG_UPT_DT | DATE | 7 | Y | 수정일자 |
| LOG_INS_ID | VARCHAR2 | 40 | Y | 생성자 |
| LOG_UPT_ID | VARCHAR2 | 40 | Y | 수정자 |
| GAIN_YN | VARCHAR2 | 1 | Y | 입고기준(B:비육 사료급이 기록,M:경영 입고기록) |
| COMP_CD | NUMBER | 22 | Y | 거래처코드 |
| ARTICLE_CD | NUMBER | 22 | Y | 품목코드 |
| FEED_CD | NUMBER | 22 | Y | 사료명코드 |
| LOC_CD | NUMBER | 22 | Y | 장소코드 |
| AUTO_GB | VARCHAR2 | 6 | Y | 저장 출처 |
| G_SEQ | NUMBER | 22 | Y | 그룹번호일련번호 |
| IN_BIGO | VARCHAR2 | 100 | Y | 등록출처 비고 |
| MP_PIG_NO | NUMBER | 22 | Y | 모돈시스템번호  |
| MOBILE | VARCHAR2 | 1 | Y | nan |


## C. 샘플 로우 (파일럿 농장 우선, 3건)

### TA_FARM


| farm_no | farm_nm | principal_nm | adm_cd | sido_cd | sigun_cd | zipcode | rnmgtsn | emdno | addr1 | addr2 | map_x | map_y | office_tel | fax | foundation | farm_type | create_dt | ict_yn | ekape_no | company_cd | sole_cd | agent_cd | jong_cd | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | etc_feed_cd | feed_ratio | country_code | money_sign | money_1000sing | money_decimalpoint | money_decimalsing | money_align | contrack_target | contrack_no | comp_acronym | cj_cd | ci_path | farm_acronym_01 | kd_file_downgb | rd_ci_path | grp_cd | alias_farm_nm | stop_dt | restart_dt | foundation_path | foundation_nm | test_yn | bill_day | info_json | manager_info | weather_nx | weather_ny | map_x_n | map_y_n | weather_nx_n | weather_ny_n | asos_stn_id | asos_stn_nm | asos_dist_km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 서해농장 | 이정학 | nan | 44 | nan | 33417 | nan | nan | 충남 보령시 주교면 용모길 57-12 |  | 126.547695030397 | 36.3886889670535 | 041-931-3161 | nan | 313-93-038 | 431004 | 2007-02-05 00:00:00 |  | 00062594 | 15 | 4 | 1 | 18.0 | Y | 2026-07-03 06:07:01 | 2026-07-03 06:07:01 | KKH | KKH |  |  | KOR |  | , | 0 | . | right | 934002 |  |  |  |  |  |  |  | 020001 |  | 9999-12-31 00:00:00 |  |  |  | N | 31 | {"serviceCodes":"2019001,2019008","ekape | [{"name":"이서현이사","tel":"010-6404-2336"," |  |  | 126.542639044194 | 36.3775995942958 | 53 | 101 |  |  |  |
| 978 | (유)무럭이농장 | 손주영 | 5277031025 | 52 | 52770 | 56016 | 3278028 | 31025 | 전북특별자치도 순창군 인계면 세심로 216 |  | 127.166850886915 | 35.4419512437234 | 063-653-8835 | 063-653-5022 | 407-81-24672 | 431002 | 2008-11-03 00:00:00 |  | nan | 15 | 5 | 1 | 52.0 | Y | 2026-03-23 07:34:31 | 2026-03-23 07:34:31 | KKH | admin0816 |  |  | KOR |  | , | 0 | . | right | 934002 |  |  |  |  |  |  |  | 020001 |  | 9999-12-31 00:00:00 |  |  |  | N | 31 | {"serviceCodes":"2019001,2019008","ekape | [{"name":"방정효","tel":"010-3633-3962","em |  |  | 127.164566297558 | 35.4513732174146 | 64 | 81 |  |  |  |
| 2807 | 용암축산 | 차주희 | 4688025028 | 46 | 46880 | 57212 | 4697292 | 25028 | 전남 장성군 장성읍 용암길 20-90 |  | 126.781330834343 | 35.3484166194858 | nan | nan | nan | 431003 | 2014-03-25 00:00:00 |  | nan | 16 | 1 | 1 | nan | Y | 2026-01-27 06:24:02 | 2026-01-27 06:24:02 | KKH | admin0816 |  |  | KOR |  | , | 0 | . | right | 934002 |  |  |  |  |  |  |  | 020012 |  | 9999-12-31 00:00:00 |  |  |  | N | 25 | {"serviceCodes":"2019001","ekapeInfo":{" | [{"name":"차주희","tel":"010-3610-6385","em |  |  | 126.782093899824 | 35.3368532098544 | 57 | 78 |  |  |  |


### TB_MODON


| farm_no | pig_no | farm_pig_no | pumjong_cd | igak_no | birth_dt | in_dt | in_sancha | in_gyobae_cnt | in_kg | status_cd | last_wk_dt | hyultong_no | mo_pig_no | un_pig_no | mo_hyul_no | un_hyul_no | out_dt | out_gubun_cd | out_reason_cd | out_reason_detail | out_kg | rfid_no | pss | family_cd | bigo | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | sale_price | in_loc_cd | buy_com_cd | move_in_gubun | move_farm_no | move_out_pig_no | mobile | mobile_die | log_upt_id_die | log_upt_dt_die | ekape_sow_no | sale_com_cd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 6767 | 03-33A | 041009 |  | 2022-03-31 00:00:00 | 2022-09-01 00:00:00 | 0 | 0 | 0.0 | 010001 |  |  |  |  |  |  | 2025-06-04 00:00:00 | 080001 | 031003 |  | 0.0 |  |  |  |  | Y | 2022-09-20 08:15:27 | 2022-09-20 08:15:27 | west001 | west001 | 0.0 |  | 51 |  |  |  |  |  | west001 | 2025-06-11 07:35:41 |  | 42 |
| 848 | 6768 | 03-82 | 041009 |  | 2022-03-30 00:00:00 | 2022-09-01 00:00:00 | 0 | 0 | 0.0 | 010001 |  |  |  |  |  |  | 2024-08-07 00:00:00 | 080001 | 031073 |  | 0.0 |  |  |  |  | Y | 2022-09-20 08:15:37 | 2022-09-20 08:15:37 | west001 | west001 | 0.0 |  | 51 |  |  |  |  |  | west001 | 2024-08-16 04:07:37 |  | 42 |
| 848 | 6778 | 01-06 | 041009 |  | 2022-03-25 00:00:00 | 2022-09-01 00:00:00 | 0 | 0 | 0.0 | 010001 |  |  |  |  |  |  | 2025-10-22 00:00:00 | 080001 | 031124 |  | 0.0 |  |  |  |  | Y | 2022-09-20 08:17:28 | 2022-09-20 08:17:28 | west001 | west001 | 0.0 |  | 51 |  |  |  |  |  | west001 | 2025-11-04 03:08:59 |  | 42 |


### TB_UNGDON


| farm_no | pig_no | farm_pig_no | igak_no | birth_dt | in_dt | jasan_dt | pumjong_cd | gubun_cd | in_kg | hyultong_no | mo_pig_no | un_pig_no | mo_hyul_no | un_hyul_no | out_dt | out_gubun_cd | out_reason_cd | out_reason_detail | out_kg | sale_price | rfid_no | pss | family_cd | bigo | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | buy_com_cd | move_in_gubun | move_farm_no | move_out_pig_no | mobile | mobile_die | log_upt_id_die | log_upt_dt_die | sale_com_cd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 1 | 0-0 |  | 2000-01-01 00:00:00 | 2000-01-01 00:00:00 |  | 042001 | 060003 |  |  |  |  |  |  | 2007-07-25 00:00:00 | 080002 |   |  | 0.0 |  |  |  |  |  | Y | 2007-02-05 22:48:10 | 2007-07-25 11:45:57 | - | west001 |  |  |  |  |  |  | west001 | 2007-07-25 11:45:57 |  |
| 848 | 2 | 0143 |  | 2000-01-01 00:00:00 | 2000-01-01 00:00:00 |  | 042001 | 060003 |  |  |  |  |  |  | 9999-12-31 00:00:00 | nan | nan |  | nan |  |  |  |  |  | Y | 2007-02-05 22:48:10 | 2007-02-05 22:48:10 | - | - |  |  |  |  |  |  | nan | NaT |  |
| 848 | 3 | 1042 |  | 2000-01-01 00:00:00 | 2000-01-01 00:00:00 |  | 042001 | 060003 |  |  |  |  |  |  | 9999-12-31 00:00:00 | nan | nan |  | nan |  |  |  |  |  | Y | 2007-02-05 22:48:10 | 2007-02-05 22:48:10 | - | - |  |  |  |  |  |  | nan | NaT |  |


### TB_MODON_WK


| farm_no | pig_no | wk_dt | wk_gubun | wk_date | sancha | gyobae_cnt | loc_cd | sago_gubun_cd | daeri_yn | seq | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | auto_gb | fw_no | mobile | ekape_iuflag | ekape_wk_dt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 1 | 20050531 | G | 2005-05-31 00:00:00 | 0 | 1 |  | nan |  | 1 | Y | 2007-02-05 17:48:45 | 1900-01-01 00:00:00 | admin0816 | admin0816 |  |  |  |  |  |
| 848 | 1 | 20050620 | F | 2005-06-20 00:00:00 | 0 | 1 |  | 050001 |  | 2 | Y | 2007-02-05 17:48:45 | 1900-01-01 00:00:00 | admin0816 | admin0816 |  |  |  |  |  |
| 848 | 1 | 20050620 | G | 2005-06-20 00:00:00 | 0 | 2 |  | nan |  | 3 | Y | 2007-02-05 17:48:45 | 1900-01-01 00:00:00 | admin0816 | admin0816 |  |  |  |  |  |


### TB_GYOBAE


| farm_no | pig_no | wk_dt | wk_gubun | method_1 | method_2 | method_3 | ungdon_pig_no_1 | ungdon_pig_no_2 | ungdon_pig_no_3 | ufarm_pig_no_1 | ufarm_pig_no_2 | ufarm_pig_no_3 | wk_person_cd | bigo | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | mobile |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 377 | 20070127 | G | A | A | A | 1 | 152 | 152.0 | 0-0 | 41136 | 41136 | 0004 |  | Y | 2007-02-10 09:34:32 | 2007-02-10 09:34:32 | west001 | west001 |  |
| 848 | 26 | 20070203 | G | A | A | A | 1 | 51 | 51.0 | 0-0 | 41010 | 41010 | 0004 |  | Y | 2007-02-14 20:03:21 | 2007-02-14 20:03:21 | west001 | west001 |  |
| 848 | 41 | 20060129 | G | A | A | nan | 1 | 226 | nan | nan | nan | nan | nan |  | Y | 2007-02-05 22:47:41 | 2007-02-05 22:47:41 | acodics | acodics |  |


### TB_BUNMAN


| farm_no | pig_no | wk_dt | wk_gubun | silsan | mila | sasan | bunman_gubun_cd | saengsi_kg | silsan_am | silsan_su | bigo | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | jd_igak_no | mobile |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 3028 | 19960323 | B | 8 | 0 | 0 | 070001 | 0.0 | 0 | 0 |  | Y | 2017-04-19 04:59:57 | 1900-01-01 00:00:00 | acodics | acodics |  |  |
| 848 | 3028 | 19960809 | B | 13 | 0 | 0 | 070001 | 0.0 | 0 | 0 |  | Y | 2017-04-19 04:59:57 | 1900-01-01 00:00:00 | acodics | acodics |  |  |
| 848 | 1273 | 19960817 | B | 3 | 1 | 0 | 070001 | 0.0 | 0 | 0 |  | Y | 2017-04-19 04:59:57 | 1900-01-01 00:00:00 | acodics | acodics |  |  |


### TB_EU


| farm_no | pig_no | wk_dt | wk_gubun | dusu | dusu_su | ilryung | total_kg | daeri_yn | bigo | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | mobile |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 1 | 20051107 | E | 13 | 0 | 0.0 | 0.0 | N |  | Y | 2007-02-05 22:48:06 | 2007-02-05 22:48:06 | acodics | acodics |  |
| 848 | 1 | 20060406 | E | 10 | 0 | 0.0 | 0.0 | N |  | Y | 2007-02-05 22:48:06 | 2007-02-05 22:48:06 | acodics | acodics |  |
| 848 | 1 | 20060831 | E | 10 | 0 | 0.0 | 0.0 | N |  | Y | 2007-02-05 22:48:06 | 2007-02-05 22:48:06 | acodics | acodics |  |


### TB_SAGO


| farm_no | pig_no | wk_dt | wk_gubun | sago_gubun_cd | bigo | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | mobile |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 1 | 20050620 | F | 050001 |  | Y | 2007-02-05 22:47:48 | 2007-02-05 22:47:48 | acodics | acodics |  |
| 848 | 2 | 20050822 | F | 050001 |  | Y | 2007-02-05 22:47:48 | 2007-02-05 22:47:48 | acodics | acodics |  |
| 848 | 2 | 20070102 | F | 050002 |  | Y | 2007-02-05 22:47:48 | 2007-02-05 22:47:48 | acodics | acodics |  |


### TB_MODON_JADON_TRANS


| farm_no | pig_no | seq | sancha | gubun_cd | sub_gubun_cd | wk_dt | dusu | dusu_su | ilryung | total_kg | bun_dt | eu_dt | io_pig_no | loc_cd | fw_no | bigo | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | auto_gb | io_seq | mobile |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 1 | 1 | 1 | 160003 | 050001 | 2005-10-14 00:00:00 | 8 | 0 | 0 | 0.0 |  |  |  |  |  |  | Y | 2017-06-22 10:17:20 | 1900-01-01 00:00:00 | acodics | acodics |  |  |  |
| 848 | 1 | 2 | 2 | 160001 | 032001 | 2006-03-05 00:00:00 | 1 | 0 | 0 | 0.0 |  |  |  |  |  |  | Y | 2017-06-22 10:17:10 | 1900-01-01 00:00:00 | acodics | acodics |  |  |  |
| 848 | 1 | 3 | 2 | 160003 | 050001 | 2006-03-05 00:00:00 | 4 | 0 | 0 | 0.0 |  |  |  |  |  |  | Y | 2017-06-22 10:17:10 | 1900-01-01 00:00:00 | acodics | acodics |  |  |  |


### TG_BUN_JADON


| farm_no | jadon_pig_no | insik_no | birth_dt | sex | pumjong_cd | saengsi_kg | sancha | hyultong_no | dung_print_yn | hyultong_in_yn | teat_left | teat_right | rfid_no | mp_pig_no | mo_pig_no | un_pig_no | mo_hyul_no | un_hyul_no | family_cd | out_dt | out_gubun_cd | ewk_dt | room_no | chamber_no | end_kg | pig_length | pig_height | teat1 | teat2 | teat3 | back_depts | body_patt | leg_patt | vulva | teat_patt | fat1 | fat2 | fat3 | day_kg | feed_eff | kg90 | week | prep1 | prep2 | prep3 | prep4 | prep5 | edays | refat | total_opi | dressed | ms | select_dt | select_cd | ungdon_idx | modon_idx | inces_idx | br_day_kg | br_fat | br_feed | br_kg90 | br_tpig | br_rpig | br_return | br_depts | br_dres | gene_pss | gene_f18 | gene_esr | use_f | esr | fabp1 | igf2 | prk3 | f4 | mc4r | br_kg90_g | br_tpig_g | br_return_g | br_feed_g | ungdon_idx_g | modon_idx_g | use_g | br_fat_h | br_kg90_h | br_tpig_h | br_return_h | br_feed_h | br_eu_h | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | out_bigo | upig_no | move_farm_no | move_dt | swk_dt | pig_length2 | back_cross_area | start_kg | user_ok_cd | mv_bigo | last_wk_dt | log_upt_dt_die | log_upt_id_die | log_upt_dt_end | log_upt_id_end | log_upt_dt_sel | log_upt_id_sel | log_upt_dt_mv | log_upt_id_mv | log_upt_dt_ht | log_upt_id_ht | back_area | movein_pig_no | jd_bigo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 9 | 106-79 | 2007-12-19 00:00:00 | 1 | 041009 | 0.0 | 8 |  | N | N |  |  |  | 371 | 12-31 | L2068 |  |  |  | 9999-12-31 00:00:00 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | Y | 2007-12-26 18:15:37 | 1900-01-01 00:00:00 | west001 | west001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 848 | 10 | 101-80 | 2007-12-19 00:00:00 | 1 | 041009 | 0.0 | 12 |  | N | N |  |  |  | 251 | 101-30 | L2068 |  |  |  | 9999-12-31 00:00:00 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | Y | 2007-12-26 18:16:09 | 1900-01-01 00:00:00 | west001 | west001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 848 | 11 | 101-81 | 2007-12-19 00:00:00 | 1 | 041009 | 0.0 | 12 |  | N | N |  |  |  | 251 | 101-30 | L2068 |  |  |  | 9999-12-31 00:00:00 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | Y | 2007-12-26 18:16:09 | 1900-01-01 00:00:00 | west001 | west001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |


### TJ_GAIN_GRP


| farm_no | grp_no | ju_gubun | grp_id | auto_yn | pumjong_cd | ilryung | sdate | edate | bigo | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | loc_cd | loc_cj_seq | mobile | bigo_end | mobile_end | sex |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 1 | J | 0630-F | N | 043009 | 28.0 | 2006-08-24 00:00:00 | 2007-06-30 00:00:00 |  | Y | 2007-03-06 16:54:56 | 2007-06-30 11:47:54 | west001 | west001 | 3056 |  |  |  |  |  |
| 848 | 2 | J | 0630-M | N | 043001 | 28.0 | 2006-08-24 00:00:00 | 2007-06-30 00:00:00 |  | Y | 2007-03-06 16:56:07 | 2007-06-30 11:48:11 | west001 | west001 | 3056 |  |  |  |  |  |
| 848 | 3 | J | 0630-W | N | 043001 | 28.0 | 2006-08-24 00:00:00 | 2007-06-30 00:00:00 |  | Y | 2007-03-06 16:55:36 | 2007-06-30 11:48:34 | west001 | west001 | 3056 |  |  |  |  |  |


### TJ_DUSU_MNG


| farm_no | grp_no | seq | ju_gubun | wk_dt | gubun_cd | sub_gubun_cd | dusu | dusu_su | total_kg | net_kg | total_price | pig_no | bigo | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | dusu1 | dusu_su1 | dusu2 | dusu_su2 | dusu3 | dusu_su3 | dusu4 | dusu_su4 | dusu5 | dusu_su5 | dusu6 | dusu_su6 | dusu7 | dusu_su7 | move_grp_no | move_farm_no | move_grp_seq | eu_seq | ilryung | batch_seq | mobile | out_com_cd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 124 | 4 | J | 2007-07-11 00:00:00 | 033 | 033001 | 1 | 0 | 0.0 |  |  |  |  | Y | 2007-07-17 11:49:53 | 2007-07-17 11:49:53 | west001 | west001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 48 |  |  |  |
| 848 | 124 | 5 | J | 2007-07-14 00:00:00 | 033 | 033001 | 1 | 0 | 0.0 |  |  |  |  | Y | 2007-07-19 10:20:39 | 2007-07-19 10:20:39 | west001 | west001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 51 |  |  |  |
| 848 | 819 | 44507 | J | 2010-05-12 00:00:00 | 033 | 033001 | 1 | 0 | 0.0 |  |  |  |  | Y | 2010-06-16 14:14:42 | 2010-06-16 14:14:42 | west001 | west001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 111 |  |  |  |


### TC_FARM_COMP


| farm_no | comp_gubun_cd | comp_nm | comp_desc | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | comp_acronym | comp_cd | cj_cd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 130001 | (주)다비육종 |  | N | 2007-02-05 16:29:41 | 2024-05-28 04:32:14 |  | west001 |  | 1 |  |
| 848 | 130001 | 서해(송악) |  | N | 2007-02-05 16:29:41 | 2007-02-05 16:29:41 |  | nan |  | 2 |  |
| 848 | 130001 | 서해농장 |  | N | 2007-02-05 16:29:41 | 2007-02-05 16:29:41 |  | nan |  | 3 |  |


### TC_FARM_CONFIG


| farm_no | code | cvalue | display_type | sort_no | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | cvalue_2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 031001 | 0 | YNYY | 2001 | Y | 2006-09-22 15:39:04 | 2012-04-09 12:54:13 |  | west001 |  |
| 848 | 031002 | 0 | YNNN | 2002 | Y | 2006-09-22 15:39:04 | 2006-09-22 15:39:04 |  | nan |  |
| 848 | 031003 | 0 | YNNN | 2003 | Y | 2006-09-22 15:39:04 | 2006-09-22 15:39:04 |  | nan |  |


### TM_ETC_TRADE


| farm_no | seq | wk_dt | account_cd | sub_gubun_cd | fper_price | total_price | price_cash | price_ncash | unit | net_kg | total_kg | grp_no | ck_use_gubun_cd | vin_cd | drug_seq | butchery_dt | validity_dt | bigo | use_yn | log_ins_dt | log_upt_dt | log_ins_id | log_upt_id | gain_yn | comp_cd | article_cd | feed_cd | loc_cd | auto_gb | g_seq | in_bigo | mp_pig_no | mobile |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 1637 | 2007-03-01 00:00:00 | 410002 |  | 1473.0 | 6775800.0 | 6775800.0 | 0.0 | 0 | 0.0 | 4600.0 |  | 100003 |  |  |  |  |  | Y | 2008-04-02 16:59:07 | 2008-04-02 16:59:07 | west001 | west001 | M | 23 |  | 1 |  |  |  |  |  |  |
| 848 | 1713 | 2007-09-01 00:00:00 | 410002 |  | 988.0 | 12844000.0 | 12844000.0 | 0.0 | 0 | 0.0 | 13000.0 |  | 100003 |  |  |  |  |  | Y | 2008-04-03 12:50:38 | 2008-04-03 12:50:38 | west001 | west001 | M | 23 |  | 2 |  |  |  |  |  |  |
| 848 | 1724 | 2007-10-01 00:00:00 | 410002 |  | 985.0 | 14775000.0 | 14775000.0 | 0.0 | 0 | 0.0 | 15000.0 |  | 100003 |  |  |  |  |  | Y | 2008-04-03 12:58:07 | 2008-04-03 12:58:07 | west001 | west001 | M | 23 |  | 2 |  |  |  |  |  |  |


## D. 코드값 사전 (가장 중요)

### TC_CODE_SYS (ko, USE_YN=Y)


| pcode | code | cname | cvalue | cvalue_2 | sort_no |
| --- | --- | --- | --- | --- | --- |
| * | 01 | 모돈상태 | nan | nan | 0.0 |
| * | 41 | 이동구분 마스터 | nan | nan | 0.0 |
| * | 42 | 그룹구분 | nan | nan | 0.0 |
| * | 43 | 농장정보 관련 | nan | nan | 0.0 |
| * | 44 | 보고서 관련 코드 | nan | nan | 0.0 |
| * | 45 | 비육돈 성적보고서 항목 | nan | nan | 0.0 |
| * | 46 | 날짜/시간 | nan | nan | 0.0 |
| * | 47 | 농가 설정정보 | nan | nan | 0.0 |
| * | 48 | 통계 정보 | nan | nan | 0.0 |
| * | 94 | 국가및언어 | nan | nan | 0.0 |
| * | 97 | 기타코드2 | nan | nan | 0.0 |
| * | 98 | 시스템 데이터 관리 | nan | nan | 0.0 |
| * | 02 | 작업 | nan | nan | nan |
| * | 03 | 목표값 | nan | nan | nan |
| * | 04 | 약품구분 | nan | nan | nan |
| * | 05 | 임신사고구분 | nan | nan | nan |
| * | 06 | 웅돈구분 | nan | nan | nan |
| * | 07 | 분만구분 | nan | nan | nan |
| * | 08 | 도폐사구분 | nan | nan | nan |
| * | 09 | 성별 | nan | nan | nan |
| * | 10 | 사료구분 | nan | nan | nan |
| * | 11 | 전입 | nan | nan | nan |
| * | 12 | 전출 | nan | nan | nan |
| * | 13 | 거래처구분 | nan | nan | nan |
| * | 14 | 농장설정 | nan | nan | nan |
| * | 15 | 작업예정돈 | nan | nan | nan |
| * | 16 | 차감구분 | nan | nan | nan |
| * | 17 | 자동그룹 | nan | nan | nan |
| * | 18 | 표준지표 | nan | nan | nan |
| * | 19 | 사용자환경설정 | nan | nan | nan |
| * | 20 | 출하 | nan | nan | nan |
| * | 21 | 재고파악 | nan | nan | nan |
| * | 22 | 비육돈사육단계 | nan | nan | nan |
| * | 23 | 비육돈작업구분 | nan | nan | nan |
| * | 24 | 교배자 | nan | nan | nan |
| * | 25 | 웅돈작업설정 | nan | nan | nan |
| * | 26 | 종돈장용코드구분 | nan | nan | nan |
| * | 27 | 검정성적보고서 | nan | nan | nan |
| * | 28 | 종돈운송방법 | nan | nan | nan |
| * | 29 | 종돈결재방법 | nan | nan | nan |
| * | 30 | 계산서 발부방법 | nan | nan | nan |
| * | 31 | 이코노팜코드 | nan | nan | nan |
| * | 32 | 이코노팜지표 | nan | nan | nan |
| * | 33 | 이코노팜비교지수 | nan | nan | nan |
| * | 34 | 년간통계모돈규모 | nan | nan | nan |
| * | 35 | 사료거래처구분 | nan | nan | nan |
| * | 36 | 자돈예정작업 | nan | nan | nan |
| * | 37 | 육성돈예정작업 | nan | nan | nan |
| * | 38 | 주사침종류 | nan | nan | nan |
| * | 39 | 소독종류 | nan | nan | nan |
| * | 40 | 소독장비 | nan | nan | nan |
| * | 90 | 시스템 제품관련 코드 | nan | nan | nan |
| * | 91 | 회원관련 코드정보 | nan | nan | nan |
| * | 93 | 계약관련 코드 | nan | nan | nan |
| * | 99 | 기타 코드 | nan | nan | nan |
| 000 | 992005 | IoT | nan | nan | 0.0 |
| 01 | 010001 | 후보돈 | nan | nan | 10.0 |
| 01 | 010002 | 임신돈 | nan | nan | 20.0 |
| 01 | 010003 | 포유돈 | nan | nan | 30.0 |
| 01 | 010004 | 대리모돈 | nan | nan | 40.0 |
| 01 | 010005 | 이유모돈 | nan | nan | 50.0 |
| 01 | 010006 | 재발돈(사고) | nan | nan | 60.0 |
| 01 | 010007 | 유산돈(사고) | nan | nan | 70.0 |
| 01 | 010008 | 도폐사돈 | nan | nan | 80.0 |
| 02 | 020001 | 출생 | nan | nan | 10.0 |
| 02 | 020002 | 전입 | nan | nan | 20.0 |
| 02 | 020003 | 교배 | nan | nan | 30.0 |
| 02 | 020004 | 분만 | nan | nan | 40.0 |
| 02 | 020005 | 이유 | nan | nan | 50.0 |
| 02 | 020006 | 대리포유 | nan | nan | 60.0 |
| 02 | 020007 | 재발불임 | nan | nan | 70.0 |
| 02 | 020008 | 유산 | nan | nan | 80.0 |
| 02 | 020098 | 도폐사/판매 | nan | nan | 90.0 |
| 02 | 020099 | 사고 | nan | nan | 100.0 |
| 02 | 020097 | 재교배 | nan | nan | 110.0 |
| 03 | 031 | 교배 | nan | nan | nan |
| 03 | 032 | 분만 | nan | nan | nan |
| 03 | 033 | 이유 | nan | nan | nan |
| 03 | 034 | 번식주기 | nan | nan | nan |
| 03 | 035 | 농장회전율 | nan | nan | nan |
| 031 | 031001 | 교배복수 | 3 | YYYN | 2001.0 |
| 031 | 031002 | 1회교배복수 | 0 | YNNN | 2002.0 |
| 031 | 031003 | 2회교배복수 | 0 | YNNN | 2003.0 |
| 031 | 031004 | 3회교배복수 | 0 | YNNN | 2004.0 |
| 031 | 031005 | 1회교배복수비율 | 0 | YNNN | 2005.0 |
| 031 | 031006 | 3회이상교배비율 | 0 | YNNN | 2006.0 |
| 031 | 031007 | 순자연교배 | 0 | YNNN | 2007.0 |
| 031 | 031008 | 순인공교배 | 0 | YNNN | 2008.0 |
| 031 | 031009 | 혼합교배 | 0 | YNNN | 2009.0 |
| 031 | 031010 | 순자연교배비율 | 0 | YNNN | 2010.0 |
| 031 | 031011 | 순인공교배비율 | 0 | YNNN | 2011.0 |
| 031 | 031012 | 혼합교배비율 | 0 | YNNN | 2012.0 |
| 031 | 031013 | 정상교배 | 0 | YNNN | 2013.0 |
| 031 | 031014 | 1차재발교배 | 0 | YNNN | 2014.0 |
| 031 | 031015 | 2차재발교배 | 0 | YNNN | 2015.0 |
| 031 | 031016 | 기타사고후교배 | 0 | YNNN | 2016.0 |
| 031 | 031017 | 미경산돈교배복수 | 0 | YNNN | 2017.0 |
| 031 | 031018 | 미경산정상교배 | 0 | YNNN | 2018.0 |
| 031 | 031019 | 미경산재발교배 | 0 | YNNN | 2019.0 |
| 031 | 031020 | 미경산기타사고후교배 | 0 | YNNN | 2020.0 |
| 031 | 031021 | 경산돈정상교배 | 0 | YNNN | 2021.0 |
| 031 | 031022 | 경산돈재발교배 | 0 | YNNN | 2022.0 |
| 031 | 031023 | 경산돈기타사고후교배 | 0 | YNNN | 2023.0 |
| 031 | 031024 | 초교배복수(모돈편입) | 0 | YYYN | 2024.0 |
| 031 | 031025 | 평균초교배일령 | 0 | YYYN | 2025.0 |
| 031 | 031026 | 재귀발정계산교배모돈수 | 0 | YNNN | 2026.0 |
| 031 | 031027 | 총재귀일수 | 0 | YNNN | 2027.0 |
| 031 | 031028 | 평균재귀발정일령 | 0 | YYYN | 2028.0 |
| 031 | 031029 | 3일내재귀복수 | 0 | YNNN | 2029.0 |
| 031 | 031030 | 4일재귀복수 | 0 | YNNN | 2030.0 |
| 031 | 031031 | 5일재귀복수 | 0 | YNNN | 2031.0 |
| 031 | 031032 | 6일재귀복수 | 0 | YNNN | 2032.0 |
| 031 | 031033 | 7일재귀복수 | 0 | YNNN | 2033.0 |
| 031 | 031034 | 8일재귀복수 | 0 | YNNN | 2034.0 |
| 031 | 031035 | 9일재귀복수 | 0 | YNNN | 2035.0 |
| 031 | 031036 | 10일이상재귀복수 | 0 | YNNN | 2036.0 |
| 031 | 031037 | 7일내재귀율 | 0 | YYYN | 2037.0 |
| 031 | 031038 | 4~6일재귀율 | 0 | YNYN | 2038.0 |
| 031 | 031039 | 재발교배비율 | 0 | YNNN | 2039.0 |
| 032 | 032001 | 분만예정복수 | 0 | YYYN | 3001.0 |
| 032 | 032002 | 임신사고1차재발 | 0 | YYYN | 3002.0 |
| 032 | 032003 | 임신사고2차재발 | 0 | YYYN | 3003.0 |
| 032 | 032004 | 임신사고기타재발 | 0 | YYYN | 3004.0 |
| 032 | 032005 | 유산(예정돈중) | 0 | YYYN | 3005.0 |
| 032 | 032006 | 도태(예정돈중) | 0 | YYYN | 3006.0 |
| 032 | 032007 | 폐사(예정돈중) | 0 | YYYN | 3007.0 |
| 032 | 032008 | 임돈전출(예정돈중) | 0 | YNNN | 3008.0 |
| 032 | 032009 | 임돈판매(예정돈중) | 0 | YYYN | 3009.0 |
| 032 | 032010 | 분만예정돈임신사고복수 | 0 | YYYN | 3010.0 |
| 032 | 032011 | 분만복수 | 0 | YYYN | 3011.0 |
| 032 | 032012 | 분만율 | 0 | YYYN | 3012.0 |
| 032 | 032013 | 보정분만율 | 0 | YYNN | 3013.0 |
| 032 | 032014 | 평균임신기간 | 0 | YYYN | 3014.0 |
| 032 | 032015 | 분만구분정상 | 0 | YNNN | 3015.0 |
| 032 | 032016 | 분만구분조산 | 0 | YYYN | 3016.0 |
| 032 | 032017 | 분만구분유도분만 | 0 | YNNN | 3017.0 |
| 032 | 032018 | 분만구분사고난산 | 0 | YNNN | 3018.0 |
| 032 | 032019 | 총산(총산자수) | 0 | YYYN | 3019.0 |
| 032 | 032020 | 실산(생존산자수) | 0 | YYYN | 3020.0 |
| 032 | 032021 | 미라 | 0 | YYNN | 3021.0 |
| 032 | 032022 | 사산 | 0 | YNNN | 3022.0 |
| 032 | 032042 | 생시도태 | 0 | YYYN | 3023.0 |
| 032 | 032023 | 미라분만모돈수 | 0 | YYNN | 3024.0 |
| 032 | 032024 | 사산분만모돈수 | 0 | YNNN | 3025.0 |
| 032 | 032043 | 생시도태분만모돈수 | 0 | YYNN | 3026.0 |
| 032 | 032025 | 평균총산 | 0 | YYYN | 3027.0 |
| 032 | 032026 | 평균실산(평균생존산자수) | 0 | YYYN | 3028.0 |
| 032 | 032027 | 생시체중측정분만복수 | 0 | YNNN | 3029.0 |
| 032 | 032028 | 생시체중측정실산자수 | 0 | YNNN | 3030.0 |
| 032 | 032029 | 평균복당생시체중 | 0 | YNNN | 3031.0 |
| 032 | 032030 | 평균자돈당생시체중 | 0 | YNNN | 3032.0 |
| 032 | 032031 | 생시자돈사고율 | 0 | YYNN | 3033.0 |
| 032 | 032032 | 사산율 | 0 | YNYN | 3034.0 |
| 032 | 032033 | 미라율 | 0 | YYYN | 3035.0 |
| 032 | 032034 | 복당생시사고두수 | 0 | YNNN | 3036.0 |
| 032 | 032035 | 복당임신사고일수 | 0 | YNYN | 3037.0 |
| 032 | 032036 | 수태율(46일까지) | 0 | YYYN | 3038.0 |
| 032 | 032037 | 평균분만간격 | 0 | YNYN | 3039.0 |
| 032 | 032038 | 분만모돈평균산차 | 0 | YYYN | 3040.0 |
| 033 | 033001 | 이유모돈두수 | 0 | YYYN | 4001.0 |
| 033 | 033002 | 이유복수(대리모포함) | 0 | YYYN | 4002.0 |
| 033 | 033003 | 이유체중측정두수비율 | 0 | YNNN | 4003.0 |
| 033 | 033004 | 보정21일령체중 | 0 | YNNN | 4004.0 |
| 033 | 033005 | 평균이유두수 | 0 | YNYN | 4005.0 |
| 033 | 033006 | 평균이유일령(대리모제외) | 0 | YYYN | 4006.0 |
| 033 | 033007 | 평균자돈당이유체중 | 0 | YNNN | 4007.0 |
| 033 | 033008 | 평균복당이유체중 | 0 | YNNN | 4008.0 |
| 033 | 033009 | 이유모돈실산자수 | 0 | YNYN | 4009.0 |
| 033 | 033010 | 양자두수 | 0 | YNNN | 4010.0 |
| 033 | 033011 | 보정21일체중측정복수 | 0 | YNNN | 4011.0 |
| 033 | 033012 | 이유체중측정이유복수 | 0 | YNNN | 4012.0 |
| 033 | 033013 | 재포유모돈두수 | 0 | YYYN | 4013.0 |
| 033 | 033014 | 이유체중측정이유자돈수 | 0 | YNNN | 4014.0 |
| 033 | 033015 | 이유전폐사율(기간중) | 0 | YYYN | 4015.0 |
| 033 | 033016 | 총보정21일령체중 | 0 | YNNN | 4016.0 |
| 033 | 033017 | 총이유일령 | 0 | YNNN | 4017.0 |
| 033 | 033018 | 총재포유자돈수 | 0 | YNNN | 4018.0 |
| 033 | 033019 | 총입력자돈폐사두수 | 0 | YNYN | 4019.0 |
| 033 | 033020 | 총이유자돈수 | 0 | YYYN | 4020.0 |
| 033 | 033021 | 총이유자돈수(부분이유포함) | 0 | YYNN | 4021.0 |
| 033 | 033022 | 이유전폐사율(실산대비이유) | 0 | YNNN | 4022.0 |
| 034 | 034001 | 총임신기간 | 0 | YNNN | 5001.0 |
| 034 | 034002 | 평균임신기간 | 0 | YNNN | 5002.0 |
| 034 | 034003 | 총포유기간 | 0 | YNNN | 5003.0 |
| 034 | 034004 | 평균복당포유기간 | 0 | YYNN | 5004.0 |
| 034 | 034005 | 전산차분만모돈수 | 0 | YNNN | 5005.0 |
| 034 | 034006 | 분만모돈두수 | 0 | YNNN | 5006.0 |
| 034 | 034007 | 총분만간격 | 0 | YNNN | 5007.0 |
| 034 | 034008 | 평균분만간격 | 0 | YNNN | 5008.0 |
| 034 | 034009 | 기간중교배두수 | 0 | YNNN | 5009.0 |
| 034 | 034010 | 분만율 | 0 | YNNN | 5010.0 |
| 034 | 034011 | 보정분만율 | 0 | YNNN | 5011.0 |
| 034 | 034012 | 총모돈사육일수(후보포함) | 0 | YNNN | 5012.0 |
| 034 | 034013 | 후보돈사육일수 | 0 | YNNN | 5013.0 |
| 034 | 034014 | 임신일수 | 0 | YNNN | 5014.0 |
| 034 | 034015 | 포유일수 | 0 | YNNN | 5015.0 |
| 034 | 034016 | 모돈생산일수(임신+포유) | 0 | YNNN | 5016.0 |
| 034 | 034017 | 총비생산일수(NPD) | 0 | YNNN | 5017.0 |
| 034 | 034018 | 후보돈포함총비생산일수 | 0 | YNNN | 5018.0 |
| 034 | 034019 | 평균비생산일수 | 0 | YYYN | 5019.0 |
| 034 | 034020 | 후보돈포함평균비생산일수 | 0 | YNYN | 5020.0 |
| 034 | 034021 | 모돈회전율(LSY) | 0 | YYYN | 5021.0 |
| 034 | 034022 | 후보돈포함모돈회전율 | 0 | YNYN | 5022.0 |
| 034 | 034023 | PSY | 0 | YYYN | 5023.0 |
| 034 | 034024 | 후보돈포함PSY | 0 | YNYN | 5024.0 |
| 034 | 034027 | 출하두수(자돈제외) | 0 | YYYN | 5025.0 |
| 034 | 034031 | 자돈출하두수 | 0 | YYYN | 5026.0 |
| 034 | 034032 | 총출하두수 | 0 | YYYN | 5027.0 |
| 034 | 034028 | 평균출하체중 | 0 | YYYN | 5028.0 |
| 034 | 034029 | MSY | 0 | YYYN | 5029.0 |
| 034 | 034025 | PSY (대모제외) | 0 | YYYN | 5030.0 |
| 034 | 034026 | 후보돈포함PSY(대모제외) | 0 | YNYN | 5031.0 |
| 034 | 034030 | MSY(자돈출하포함) | 0 | YNNN | 5032.0 |
| 035 | 035001 | 상시모돈수 | 0 | YYYN | 1001.0 |
| 035 | 035002 | 후보돈포함상시모돈수 | 0 | YYYN | 1002.0 |
| 035 | 035003 | 기말재고모돈평균산차 | 0 | YYYN | 1003.0 |
| 035 | 035004 | 도태모돈평균산차 | 0 | YYNN | 1004.0 |
| 035 | 035005 | 평균전입일령 | 0 | YNNN | 1005.0 |
| 035 | 035006 | 기초모돈재고(후보제외) | 0 | YYNN | 1006.0 |
| 035 | 035007 | 기말모돈재고(후보제외) | 0 | YYYN | 1007.0 |
| 035 | 035008 | 모돈/웅돈비율 | 0 | YNNN | 1008.0 |
| 035 | 035009 | 모돈도태율 | 0 | YYNN | 1009.0 |
| 035 | 035010 | 모돈폐사두수 | 0 | YNYN | 1010.0 |
| 035 | 035011 | 연간모돈전입율 | 0 | YYYN | 1011.0 |
| 035 | 035012 | 모돈폐사율 | 0 | YYNN | 1012.0 |
| 035 | 035013 | 모돈도폐사율 | 0 | YNNN | 1013.0 |
| 035 | 035014 | 모돈도태두수 | 0 | YNYN | 1014.0 |
| 035 | 035015 | 모돈전입두수 | 0 | YNYN | 1015.0 |
| 035 | 035016 | 모돈판매두수 | 0 | YNNN | 1016.0 |
| 035 | 035017 | 모돈전출두수 | 0 | YNNN | 1017.0 |
| 035 | 035018 | 기말자연교배웅돈수 | 0 | YNNN | 1018.0 |
| 035 | 035019 | 기말인공정액웅돈수 | 0 | YNNN | 1019.0 |
| 035 | 035020 | 기말사용웅돈재고두수 | 0 | YNYN | 1020.0 |
| 035 | 035021 | 평균전입교배간격 | 0 | YNYN | 1021.0 |
| 035 | 035022 | 기초후보돈 | 0 | YNNN | 1022.0 |
| 035 | 035023 | 기말후보돈 | 0 | YNYN | 1023.0 |
| 035 | 035024 | 총도폐사판매모돈수 | 0 | YNNN | 1024.0 |
| 035 | 035025 | 상시웅돈수 | 0 | YNNN | 1025.0 |
| 035 | 035026 | 후보포함상시웅돈수 | 0 | YNNN | 1026.0 |
| 035 | 035027 | 연간웅돈전입율 | 0 | YNNN | 1027.0 |
| 035 | 035028 | 웅돈전입두수 | 0 | YNNN | 1028.0 |
| 035 | 035029 | 기말웅돈수 | 0 | YNNN | 1029.0 |
| 04 | 040001 | 백신 | nan | nan | nan |
| 04 | 040002 | 치료제 | nan | nan | nan |
| 04 | 040003 | 항생제 | nan | nan | nan |
| 04 | 040004 | 영양제 | nan | nan | nan |
| 04 | 040005 | 홀몬제 | nan | nan | nan |
| 04 | 040006 | 구충제 | nan | nan | nan |
| 04 | 040007 | 살충제 | nan | nan | nan |
| 04 | 040008 | 소독제 | nan | nan | nan |
| 04 | 040009 | 수의기구 | nan | nan | nan |
| 04 | 040010 | 기타 | nan | nan | nan |
| 05 | 050008 | 재발 | 80 | nan | 10.0 |
| 05 | 050009 | 불임 | 90 | nan | 20.0 |
| 05 | 050007 | 공태 | 20 | nan | 30.0 |
| 05 | 050002 | 유산 | 30 | nan | 40.0 |
| 05 | 050003 | 도태 | 40 | 080001 | 50.0 |
| 05 | 050004 | 폐사 | 50 | 080002 | 60.0 |
| 05 | 050005 | 임돈전출 | 60 | 080003 | 70.0 |
| 05 | 050006 | 임돈판매 | 70 | 080004 | 80.0 |
| 05 | 050001 | (구)재발불임 | 10 | nan | 9000.0 |
| 06 | 060001 | 자연교배 | nan | nan | 1.0 |
| 06 | 060002 | 자가인공 | nan | nan | 2.0 |
| 06 | 060003 | 센터정액 | nan | nan | 3.0 |
| 07 | 070001 | 정상 | nan | nan | 1.0 |
| 07 | 070002 | 유도분만 | nan | nan | 2.0 |
| 07 | 070003 | 분만사고난산 | nan | nan | 3.0 |
| 07 | 070004 | 조산 | nan | nan | 4.0 |
| 08 | 080001 | 도태 | 050003 | nan | 1.0 |
| 08 | 080002 | 폐사 | 050004 | nan | 2.0 |
| 08 | 080003 | 전출 | 050005 | nan | 3.0 |
| 08 | 080004 | 판매 | 050006 | nan | 4.0 |
| 09 | 090001 | 암 | 1 | nan | 0.0 |
| 09 | 090002 | 수 | 2 | nan | 0.0 |
| 09 | 090003 | 거세 | nan | nan | nan |
| 09 | 090004 | 불명 | nan | nan | nan |
| 10 | 100 | 부경사료 | nan | nan | nan |
| 10 | 101 | 타사사료 | nan | nan | nan |
| 100 | 100001 | 갓돈 | nan | nan | 1.0 |
| 100 | 100002 | 젖돈 | nan | nan | 2.0 |
| 100 | 100003 | 젖뗀돈 | nan | nan | 3.0 |
| 100 | 100004 | 육성돈 | nan | nan | 4.0 |
| 100 | 100005 | 비육돈 | nan | nan | 5.0 |
| 100 | 100006 | 임신돈 | nan | nan | 6.0 |
| 100 | 100007 | 포유돈 | nan | nan | 7.0 |
| 100 | 100008 | 기타 | nan | nan | 8.0 |
| 101 | 101001 | 갓돈 | nan | nan | nan |
| 101 | 101002 | 젖돈 | nan | nan | nan |
| 101 | 101003 | 젖뗀돈 | nan | nan | nan |
| 101 | 101004 | 육성돈 | nan | nan | nan |
| 101 | 101005 | 비육돈 | nan | nan | nan |
| 101 | 101006 | 임신돈 | nan | nan | nan |
| 101 | 101007 | 포유돈 | nan | nan | nan |
| 101 | 101008 | 기타 | nan | nan | nan |
| 11 | 110001 | 이유입식 | nan | nan | 100.0 |
| 11 | 110002 | 자돈구입 | nan | nan | 200.0 |
| 11 | 110003 | 농장내이동 | nan | nan | 300.0 |
| 11 | 110007 | 농장내이동(비육사) | nan | nan | 310.0 |
| 11 | 110004 | 위탁(계열)전입 | nan | nan | 400.0 |
| 11 | 110005 | 부분이유입식 | nan | nan | 500.0 |
| 12 | 120001 | 위탁(계열)전출 | nan | nan | 100.0 |
| 12 | 120002 | 위축돈이동 | nan | nan | 200.0 |
| 12 | 120003 | 농장내이동 | nan | nan | 300.0 |
| 12 | 120004 | 농장내이동(비육사) | nan | nan | 400.0 |
| 12 | 120005 | 농장내이동(검정사) | nan | nan | 500.0 |
| 13 | 130001 | 종돈거래처 | nan | nan | 1.0 |
| 13 | 130002 | 사료거래처 | nan | nan | 2.0 |
| 13 | 130003 | 출하거래처 | nan | nan | 3.0 |
| 13 | 130004 | 약품거래처 | nan | nan | 4.0 |
| 13 | 130005 | 자돈거래처 | nan | nan | 5.0 |
| 13 | 130006 | 기타거래처 | nan | nan | 6.0 |
| 13 | 130007 | 소모품거래처 | nan | nan | 7.0 |
| 13 | 130008 | 보조재료거래처 | nan | nan | 8.0 |
| 13 | 130009 | 육성돈거래처 | nan | nan | 9.0 |
| 13 | 130010 | 번식돈거래처 | nan | nan | 10.0 |
| 13 | 130011 | 일괄사육거래처 | nan | nan | 11.0 |
| 13 | 130012 | 정액판매거래처 | nan | nan | 12.0 |
| 14 | 140015 | HACCP사용여부 | N | HA | 0.0 |
| 14 | 140020 | 분만두수산출기준 | S | nan | 0.0 |
| 14 | 140025 | 장소별일괄등록(돈사구분) | nan | JD-LOC-BATCH | 0.0 |
| 14 | 140026 | 장소별일괄등록(전출) | nan | JD-LOC-BATCH | 0.0 |
| 14 | 140027 | 장소별일괄등록(출하) | nan | JD-LOC-BATCH | 0.0 |
| 14 | 140028 | 장소별일괄등록(품종) | nan | JD-LOC-BATCH | 0.0 |
| 14 | 140001 | 최대허용산차 | 20 | MD | 100.0 |
| 14 | 140030 | 자돈비육돈 관리유형 | 472001 | JD | 100.0 |
| 14 | 140002 | 평균임신기간 | 115 | MD | 200.0 |
| 14 | 140021 | 그룹 일령산출기준 | 471002 | JD | 200.0 |
| 14 | 140031 | 일괄등록 다중처리</br>(전출/출하) | Y | JD | 220.0 |
| 14 | 140003 | 평균포유기간 | 21 | MD | 300.0 |
| 14 | 140019 | 그룹종료여부 | Y | JD | 300.0 |
| 14 | 140024 | 출하구분 설정 | [{"outGubunYn":"Y","report":"biuk","shipment":"200001","management":"5 | JD | 300.0 |
| 14 | 140008 | 평균재귀일 | 7 | MD | 400.0 |
| 14 | 140012 | 기준규격체중 | 100 | JD | 400.0 |
| 14 | 140029 | 비육돈 돈사구분 | 080005,080006,080007,080008,080009 | JD | 400.0 |
| 14 | 140004 | 기준출하체중 | 110 | JD | 500.0 |
| 14 | 140018 | 후보돈초교배평균재발정일 | 20 | MD | 500.0 |
| 14 | 140005 | 기준출하일령 | 180 | JD | 600.0 |
| 14 | 140006 | 후보돈초발정체크일령 | 180 | MD | 600.0 |
| 14 | 140007 | 후보돈초교배일령 | 240 | MD | 700.0 |
| 14 | 140009 | 교배요일 | 461002 | MD | 800.0 |
| 14 | 140010 | 분만요일 | 461004 | MD | 900.0 |
| 14 | 140011 | 이유요일 | 461006 | MD | 1100.0 |
| 14 | 140016 | 번식사이동일수 | 50 | MD | 1200.0 |
| 14 | 140017 | 임신사이동일수 | 115 | MD | 1300.0 |
| 14 | 140013 | 양자상대모돈기입여부 | Y | MD | 1400.0 |
| 14 | 140014 | 번식기록 암/수 표시 | Y | MD | 1500.0 |
| 14 | 140022 | 총산 자동생성(분만기록) | N | MD | 1600.0 |
| 14 | 140023 | 도폐사 수익연동 | 080001,080004 | MD | 1700.0 |
| 15 | 150001 | 임신 감정돈(진단) | RpdWorkScheduleModon03 | nan | 0.0 |
| 15 | 150002 | 분만 예정돈 | RpdWorkScheduleModon04 | nan | 0.0 |
| 15 | 150003 | 이유 예정돈 | RpdWorkScheduleModon05 | nan | 0.0 |
| 15 | 150004 | 백신 예정돈 | RpdWorkScheduleModon06 | nan | 0.0 |
| 15 | 150005 | 교배 대기돈 | RpdWorkScheduleModon01 | nan | 0.0 |
| 15 | 150006 | 이유예정 자돈 | nan | nan | 0.0 |
| 15 | 150007 | 백신예정 자돈 | RpdWorkScheduleModon07 | nan | 0.0 |
| 16 | 160001 | 포유자돈폐사 | nan | nan | nan |
| 16 | 160002 | 부분이유 | nan | nan | nan |
| 16 | 160003 | 양자전입 | nan | nan | nan |
| 16 | 160004 | 양자전출 | nan | nan | nan |
| 17 | 170001 | 자동그룹구분 | nan | nan | nan |
| 17 | 170002 | 자동그룹표시형식 | nan | nan | nan |
| 18 | 181 | 표준모돈구성비율 | nan | nan | nan |
| 18 | 182 | 비육돈주령별체중 | nan | nan | nan |
| 18 | 183 | 모돈산차별체중 | nan | nan | nan |
| 18 | 184 | 웅돈개월별체중 | nan | nan | nan |
| 18 | 185 | 비육돈주령별음수량 | nan | nan | nan |
| 181 | 181001 | 후보돈비율 | 10.3 | -1 | 0.0 |
| 181 | 181002 | 0산비율 | 14.4 | 0 | nan |
| 181 | 181003 | 1산비율 | 19.7 | 1 | nan |
| 181 | 181004 | 2산비율 | 16.2 | 2 | nan |
| 181 | 181005 | 3산비율 | 15.1 | 3 | nan |
| 181 | 181006 | 4산비율 | 11.5 | 4 | nan |
| 181 | 181007 | 5산비율 | 7.2 | 5 | nan |
| 181 | 181008 | 6산비율 | 6.4 | 6 | nan |
| 181 | 181009 | 7산비율 | 3.3 | 7 | nan |
| 181 | 181010 | 8산이상비율 | 6.2 | 8 | nan |
| 182 | 182001 | 1주령 | 2.6 | nan | nan |
| 182 | 182002 | 2주령 | 4.0 | nan | nan |
| 182 | 182003 | 3주령 | 5.5 | nan | nan |
| 182 | 182004 | 4주령 | 7.3 | nan | nan |
| 182 | 182005 | 5주령 | 9.0 | nan | nan |
| 182 | 182006 | 6주령 | 11.4 | nan | nan |
| 182 | 182007 | 7주령 | 14.5 | nan | nan |
| 182 | 182008 | 8주령 | 17.7 | nan | nan |
| 182 | 182009 | 9주령 | 21.3 | nan | nan |
| 182 | 182010 | 10주령 | 26.0 | nan | nan |
| 182 | 182011 | 11주령 | 30.9 | nan | nan |
| 182 | 182012 | 12주령 | 35.8 | nan | nan |
| 182 | 182013 | 13주령 | 40.7 | nan | nan |
| 182 | 182014 | 14주령 | 45.6 | nan | nan |
| 182 | 182015 | 15주령 | 50.6 | nan | nan |
| 182 | 182016 | 16주령 | 56.3 | nan | nan |
| 182 | 182017 | 17주령 | 62.1 | nan | nan |
| 182 | 182018 | 18주령 | 67.8 | nan | nan |
| 182 | 182019 | 19주령 | 73.6 | nan | nan |
| 182 | 182020 | 20주령 | 79.3 | nan | nan |
| 182 | 182021 | 21주령 | 85.0 | nan | nan |
| 182 | 182022 | 22주령 | 90.8 | nan | nan |
| 182 | 182023 | 23주령 | 96.6 | nan | nan |
| 182 | 182024 | 24주령 | 102.3 | nan | nan |
| 182 | 182025 | 25주령 | 108.0 | nan | nan |
| 182 | 182026 | 26주령 | 113.7 | nan | nan |
| 182 | 182027 | 27주령 | 119.5 | nan | nan |
| 182 | 182028 | 28주령 | 125.2 | nan | nan |
| 183 | 183001 | 0산체중 | 90.0 | nan | nan |
| 183 | 183002 | 1산체중 | 130.0 | nan | nan |
| 183 | 183003 | 2산체중 | 160.0 | nan | nan |
| 183 | 183004 | 3산체중 | 180.0 | nan | nan |
| 183 | 183005 | 4산체중 | 200.0 | nan | nan |
| 183 | 183006 | 5산체중 | 220.0 | nan | nan |
| 183 | 183007 | 6산이상체중 | 230.0 | nan | nan |
| 184 | 184001 | 6개월미만 | 80.0 | nan | nan |
| 184 | 184002 | 6개월이상-18개월미만 | 130.0 | nan | nan |
| 184 | 184003 | 18개월이상-30개월미만 | 200.0 | nan | nan |
| 184 | 184004 | 30개월이상 | 250.0 | nan | nan |
| 185 | 185001 | 1주령 | 0.1 | nan | nan |
| 185 | 185002 | 2주령 | 0.2 | nan | nan |
| 185 | 185003 | 3주령 | 0.3 | nan | nan |
| 185 | 185004 | 4주령 | 0.4 | nan | nan |
| 185 | 185005 | 5주령 | 0.6 | nan | nan |
| 185 | 185006 | 6주령 | 0.7 | nan | nan |
| 185 | 185007 | 7주령 | 0.9 | nan | nan |
| 185 | 185008 | 8주령 | 1 | nan | nan |
| 185 | 185009 | 9주령 | 2.5 | nan | nan |
| 185 | 185010 | 10주령 | 3.3 | nan | nan |
| 185 | 185011 | 11주령 | 3.6 | nan | nan |
| 185 | 185012 | 12주령 | 4.2 | nan | nan |
| 185 | 185013 | 13주령 | 4.6 | nan | nan |
| 185 | 185014 | 14주령 | 5 | nan | nan |
| 185 | 185015 | 15주령 | 5.7 | nan | nan |
| 185 | 185016 | 16주령 | 6.4 | nan | nan |
| 185 | 185017 | 17주령 | 7 | nan | nan |
| 185 | 185018 | 18주령 | 7.5 | nan | nan |
| 185 | 185019 | 19주령 | 8 | nan | nan |
| 185 | 185020 | 20주령 | 8.5 | nan | nan |
| 185 | 185021 | 21주령 | 8.9 | nan | nan |
| 185 | 185022 | 22주령 | 9.3 | nan | nan |
| 185 | 185023 | 23주령 | 9.8 | nan | nan |
| 185 | 185024 | 24주령 | 10.3 | nan | nan |
| 185 | 185025 | 25주령 | 10.3 | nan | nan |
| 185 | 185026 | 26주령 | 10.3 | nan | nan |
| 185 | 185027 | 27주령 | 10.3 | nan | nan |
| 185 | 185028 | 28주령 | 10.3 | nan | nan |
| 19 | 190001 | 산차출력구분 | 0,1,2,3,4,5,6,7,8+ | nan | nan |
| 19 | 190002 | 포유일수출력구분 | 1-15,16,17,18,19,20,21,22,23,24,25+ | nan | nan |
| 20 | 200001 | 가공 | 511001 | nan | 100.0 |
| 20 | 200002 | 탕박경매 | 511002 | nan | 200.0 |
| 20 | 200003 | 자돈출하 | 513001 | nan | 300.0 |
| 20 | 200004 | 개인상인판매 | 511004 | nan | 400.0 |
| 20 | 200005 | 종돈출하 | 514001 | nan | 500.0 |
| 20 | 200006 | 박피경매 | 511003 | nan | 600.0 |
| 20 | 200007 | 농장내판매 | 514001 | nan | 700.0 |
| 20 | 200008 | 비육출하 | 513001 | nan | 800.0 |
| 20 | 200009 | 도태출하 | 513001 | nan | 900.0 |
| 22 | 220001 | 젖뗀돈 | nan | nan | nan |
| 22 | 220002 | 육성돈 | nan | nan | nan |
| 22 | 220003 | 비육전기 | nan | nan | nan |
| 22 | 220004 | 비육후기 | nan | nan | nan |
| 23 | 230001 | 백신작업 | nan | nan | nan |
| 23 | 230002 | 출하작업 | nan | nan | nan |
| 25 | 250001 | 백신작업 | nan | nan | nan |
| 25 | 250002 | 정액채취 | nan | nan | nan |
| 26 | 260001 | 종돈선발구분 | nan | nan | nan |
| 26 | 260002 | 지역구분 | nan | nan | nan |
| 26 | 260003 | 농가구분 | nan | nan | nan |
| 26 | 260004 | 조합구분 | nan | nan | nan |
| 26 | 260005 | 판매돈구분(품종) | nan | nan | nan |
| 26 | 260006 | 돈구분 | nan | nan | nan |
| 26 | 260007 | 인수장소(돈사) | nan | nan | nan |
| 26 | 260008 | 약품출고구분 | nan | nan | nan |
| 26 | 260009 | 약품입고구분 | nan | nan | nan |
| 26 | 260010 | 수금회사 | nan | nan | nan |
| 26 | 260011 | 관리구분 | nan | nan | nan |
| 26 | 260012 | AI구분 | nan | nan | nan |
| 26 | 260013 | 신규구분 | nan | nan | nan |
| 26 | 260014 | 방문자 | nan | nan | nan |
| 26 | 260015 | 방문목적 | nan | nan | nan |
| 26 | 260016 | 운송방법 | nan | nan | nan |
| 27 | 272 | 데이터 분석항목 | nan | nan | 0.0 |
| 27 | 271 | 표현형가 정보 | nan | nan | nan |
| 271 | 271001 | 개체번호 | S | nan | nan |
| 271 | 271002 | 품종 | S | nan | nan |
| 271 | 271003 | 부돈번호 | S | nan | nan |
| 271 | 271004 | 모돈번호 | S | nan | nan |
| 271 | 271005 | 부돈가계 | S | nan | nan |
| 271 | 271006 | 모돈가계 | S | nan | nan |
| 271 | 271007 | 자돈가계 | S | nan | nan |
| 271 | 271008 | 성별 | SEX | nan | nan |
| 271 | 271009 | 산차 | I | nan | nan |
| 271 | 271010 | 생년월일 | D | nan | nan |
| 271 | 271011 | 총산자수 | F | nan | nan |
| 271 | 271012 | 실산자수 | F | nan | nan |
| 271 | 271013 | 발정재귀일수 | F | nan | nan |
| 271 | 271014 | 검정개시일자 | D | nan | nan |
| 271 | 271015 | 검정개시일령 | I | nan | nan |
| 271 | 271016 | 검정개시체중 | F | nan | nan |
| 271 | 271017 | 검정종료일자 | D | nan | nan |
| 271 | 271018 | 검정종료일령 | I | nan | nan |
| 271 | 271019 | 검정종료체중 | F | nan | nan |
| 271 | 271020 | 등지방1 | F | nan | nan |
| 271 | 271021 | 등지방2 | F | nan | nan |
| 271 | 271022 | 등지방3 | F | nan | nan |
| 271 | 271023 | 보정등지방 | F | nan | nan |
| 271 | 271024 | 일당증체중 | F | nan | nan |
| 271 | 271025 | 90KG도달일령 | F | nan | nan |
| 271 | 271026 | 체장 | F | nan | nan |
| 271 | 271027 | 체고 | F | nan | nan |
| 271 | 271028 | 등심단면적 | F | nan | nan |
| 271 | 271029 | 정육율 | F | nan | nan |
| 271 | 271030 | 사료요구율 | F | nan | nan |
| 271 | 271031 | 유두수(좌) | F | nan | nan |
| 271 | 271032 | 유두수(우) | F | nan | nan |
| 271 | 271033 | 유두수(부/맹) | F | nan | nan |
| 271 | 271034 | 호실 | S | nan | nan |
| 271 | 271035 | 돈방 | S | nan | nan |
| 271 | 271036 | 체형 | F | nan | nan |
| 271 | 271037 | 지제 | F | nan | nan |
| 271 | 271038 | 외음부 | F | nan | nan |
| 271 | 271039 | 유두형태 | F | nan | nan |
| 271 | 271040 | 종합평가 | S | nan | nan |
| 271 | 271041 | 기타항목1 | S | nan | nan |
| 271 | 271042 | 기타항목2 | S | nan | nan |
| 271 | 271043 | 기타항목3 | S | nan | nan |
| 271 | 271044 | 기타항목4 | S | nan | nan |
| 271 | 271045 | 기타항목5 | S | nan | nan |
| 271 | 271046 | 선발일자 | D | nan | nan |
| 271 | 271047 | 선발내용 | S | nan | nan |
| 271 | 271048 | 동복총산자수 | I | nan | nan |
| 272 | 272001 | 등지방(표현) | REFAT | nan | 1.0 |
| 272 | 272002 | 일당증체량(표현) | DAY_KG | nan | 2.0 |
| 272 | 272003 | 90Kg도달일령(표현) | KG90 | nan | 3.0 |
| 272 | 272004 | 체장 | PIG_LENGTH | nan | 4.0 |
| 272 | 272005 | 체고 | PIG_HEIGHT | nan | 5.0 |
| 272 | 272006 | 등심(표현) | BACK_DEPTS | nan | 6.0 |
| 272 | 272007 | 정육율(표현) | DRESSED | nan | 7.0 |
| 272 | 272008 | 등지방(육종) | BR_FAT | nan | 8.0 |
| 272 | 272009 | 일당증체량(육종) | BR_DAY_KG | nan | 9.0 |
| 272 | 272010 | 90Kg도달일령(육종) | BR_KG90 | nan | 10.0 |
| 272 | 272011 | 사료요구율(육종) | BR_FEED | nan | 11.0 |
| 272 | 272012 | 총산(육종) | BR_TPIG | nan | 12.0 |
| 272 | 272013 | 실산(육종) | BR_RPIG | nan | 13.0 |
| 272 | 272014 | 발정재귀일(육종) | BR_RETURN | nan | 14.0 |
| 272 | 272015 | 부계지수(육종) | UNGDON_IDX | nan | 15.0 |
| 272 | 272016 | 모계지수(육종) | MODON_IDX | nan | 16.0 |
| 272 | 272017 | 근친도(육종) | INCES_IDX | nan | 17.0 |
| 28 | 280001 | 자차 | 278 | nan | 0.0 |
| 28 | 280002 | 용차 | 280 | nan | 0.0 |
| 28 | 280003 | 택배 | 282 | nan | 0.0 |
| 28 | 280004 | 김건우 | 284 | nan | 0.0 |
| 28 | 280005 | 김세환 | 326 | nan | 0.0 |
| 28 | 280006 | 미래물류 | 340 | nan | 0.0 |
| 28 | 280007 | 명천 | 372 | nan | 0.0 |
| 28 | 280008 | 이화운송 | 384 | nan | 0.0 |
| 29 | 290001 | 현금 | nan | nan | 10.0 |
| 29 | 290003 | 카드 | nan | nan | 20.0 |
| 29 | 290002 | 외상 | nan | nan | 30.0 |
| 30 | 300001 | 월단위 | nan | nan | nan |
| 30 | 300002 | 년단위 | nan | nan | nan |
| 31 | 310001 | 판매본부 | nan | nan | 0.0 |
| 31 | 310003 | 관리담당자 | nan | nan | 0.0 |
| 31 | 310002 | 업체구분 | nan | nan | nan |
| 31 | 310004 | 지육단가종류 | nan | nan | nan |
| 31 | 310005 | 사료비율종류 | nan | nan | nan |
| 31 | 310006 | 지육율 | nan | nan | nan |
| 32 | 321 | 번식지표 | nan | nan | nan |
| 32 | 322 | 비육지표 | nan | nan | nan |
| 32 | 323 | 매출액지표 | nan | nan | nan |
| 32 | 324 | 경영비지표 | nan | nan | nan |
| 32 | 325 | 이익지표 | nan | nan | nan |
| 32 | 326 | 경영비율 | nan | nan | nan |
| 321 | 321001 | 상시모돈 | 100 | nan | nan |
| 321 | 321002 | 분만율 | 85 | nan | nan |
| 321 | 321003 | 모돈회전율 | 2.2 | nan | nan |
| 321 | 321004 | 복당이유두수 | 9.5 | nan | nan |
| 321 | 321005 | PSY | 23 | nan | nan |
| 322 | 322001 | 육성율 | 0 | nan | nan |
| 322 | 322002 | 출하평체 | 0 | nan | nan |
| 322 | 322003 | MSY | 0 | nan | nan |
| 322 | 322004 | WSY | 0 | nan | nan |
| 323 | 323001 | FCR | 0 | nan | nan |
| 323 | 323002 | 사료단가 | 0 | nan | nan |
| 323 | 323003 | 증체KG당사료비 | 0 | nan | nan |
| 323 | 323004 | 출하두당사료비 | 0 | nan | nan |
| 323 | 323005 | 출하두당경영비 | 0 | nan | nan |
| 324 | 324001 | 출하두당매출액 | 0 | nan | nan |
| 324 | 324002 | 판매지육단가 | 0 | nan | nan |
| 325 | 325001 | 출하두당순이익 | 0 | nan | nan |
| 325 | 325002 | 월순이익 | 0 | nan | nan |
| 325 | 325003 | 수익분기지육단가 | 0 | nan | nan |
| 33 | 330001 | 모돈회전율 | nan | nan | nan |
| 33 | 330002 | 분만율 | nan | nan | nan |
| 33 | 330003 | 복당이유두수 | nan | nan | nan |
| 33 | 330004 | PwSY | nan | nan | nan |
| 33 | 330005 | PmSY | nan | nan | nan |
| 33 | 330006 | 사료요구율 | nan | nan | nan |
| 33 | 330007 | WSY | nan | nan | nan |
| 34 | 340001 | 100두 미만 | nan | nan | 10.0 |
| 34 | 340002 | 100두 규모 | nan | nan | 20.0 |
| 34 | 340003 | 200두 규모 | nan | nan | 30.0 |
| 34 | 340004 | 300두 규모 | nan | nan | 40.0 |
| 34 | 340005 | 400두 규모 | nan | nan | 50.0 |
| 34 | 340006 | 500두 규모 | nan | nan | 60.0 |
| 34 | 340007 | 600두 규모 | nan | nan | 70.0 |
| 34 | 340008 | 700두 규모 | nan | nan | 80.0 |
| 34 | 340009 | 800두 규모 | nan | nan | 90.0 |
| 34 | 340010 | 900두 규모 | nan | nan | 100.0 |
| 34 | 340011 | 1000두 이상 | nan | nan | 110.0 |
| 35 | 350001 | 주거래사료 | nan | nan | nan |
| 35 | 350002 | 타사사료 | nan | nan | nan |
| 36 | 360001 | 백신작업 | nan | nan | nan |
| 36 | 360002 | 출하작업 | nan | nan | nan |
| 37 | 370001 | 백신작업 | nan | nan | nan |
| 37 | 370002 | 출하작업 | nan | nan | nan |
| 38 | 380001 | 18G장침 | nan | nan | nan |
| 38 | 380002 | 19G장침 | nan | nan | nan |
| 38 | 380003 | 18G단침 | nan | nan | nan |
| 38 | 380004 | 21G단침 | nan | nan | nan |
| 39 | 390001 | 분무소독 | nan | nan | nan |
| 39 | 390002 | 훈증소독 | nan | nan | nan |
| 39 | 390003 | 도포소독 | nan | nan | nan |
| 40 | 400001 | 동력분무기 | nan | nan | nan |
| 40 | 400002 | 고압세척기 | nan | nan | nan |
| 41 | 4102 | 전출 | 12 | nan | 2.0 |
| 41 | 4103 | 출하 | 20 | nan | 3.0 |
| 41 | 4104 | 반품 | 13 | nan | 4.0 |
| 42 | 420100 | 자돈 그룹 | J | nan | 1.0 |
| 42 | 420200 | 비육돈 그룹 | U | nan | 2.0 |
| 43 | 431 | 농장종류 | nan | nan | 0.0 |
| 431 | 431003 | 일괄사육장 | B | nan | 100.0 |
| 431 | 431004 | 번식농장 | C | nan | 200.0 |
| 431 | 431005 | 비육농장 | D | nan | 300.0 |
| 431 | 431001 | 종돈장(GGP) | A | nan | 400.0 |
| 431 | 431002 | GP농장 | E | nan | 500.0 |
| 431 | 431006 | AI센터 | F | nan | 600.0 |
| 431 | 431007 | 스마트팜 | S | nan | 700.0 |
| 44 | 441 | 출력구분 | nan | nan | 0.0 |
| 44 | 442 | 출력항목 | nan | nan | 0.0 |
| 44 | 443 | 비육돈 출력구분 | nan | nan | 0.0 |
| 441 | 441001 | 기간별 | nan | nan | 1.0 |
| 441 | 441002 | 산차별 | nan | nan | 2.0 |
| 441 | 441003 | 품종별 | nan | nan | 3.0 |
| 442 | 442001 | 전체 | 1 | nan | 1.0 |
| 442 | 442002 | 기본형 | 2 | nan | 2.0 |
| 442 | 442003 | 핵심형1 | 3 | nan | 3.0 |
| 442 | 442004 | 핵심형2 | 4 | nan | 4.0 |
| 443 | 443001 | 진행그룹 | nan | nan | 1.0 |
| 443 | 443002 | 종료그룹 | nan | nan | 2.0 |
| 45 | 451 | 비육돈 성적비교 보고서 | nan | nan | 1.0 |
| 45 | 452 | 비육돈 기간별 성적분석 보고서 | nan | nan | 2.0 |
| 451 | 451001 | 예상그룹종료일자 | nan | nan | 1.0 |
| 451 | 451002 | 그룹시작일자 | nan | nan | 2.0 |
| 451 | 451003 | 기말재고두수 | nan | nan | 3.0 |
| 451 | 451004 | 구입두수 | nan | nan | 4.0 |
| 451 | 451005 | 이유입식 | nan | nan | 5.0 |
| 451 | 451006 | 총전입두수 | nan | nan | 6.0 |
| 451 | 451007 | 평균전입일령 | nan | nan | 7.0 |
| 451 | 451008 | 폐사두수 | nan | nan | 8.0 |
| 451 | 451009 | 폐사율(%) | nan | nan | 9.0 |
| 451 | 451010 | 평균폐사일령 | nan | nan | 10.0 |
| 451 | 451011 | 총생체중:폐사두수 | nan | nan | 11.0 |
| 451 | 451012 | 검색최종일기준평균일령 | nan | nan | 12.0 |
| 451 | 451013 | 총생체중:총전입두수 | nan | nan | 13.0 |
| 451 | 451014 | 평균생체:총전입두수 | nan | nan | 14.0 |
| 451 | 451015 | 분양두수 | nan | nan | 15.0 |
| 451 | 451016 | 출하두수 | nan | nan | 16.0 |
| 451 | 451017 | 전출두수 | nan | nan | 17.0 |
| 451 | 451018 | 총사료입고량 | nan | nan | 18.0 |
| 451 | 451019 | 예상총사료사용량 | nan | nan | 19.0 |
| 451 | 451020 | 예상사료요구율 | nan | nan | 20.0 |
| 451 | 451021 | 예상사료금액 | nan | nan | 21.0 |
| 451 | 451022 | 평균1일 사료섭취량 | nan | nan | 22.0 |
| 452 | 452001 | 기간일수 | 1 | nan | 1.0 |
| 452 | 452002 | 기초두수 | 2 | nan | 2.0 |
| 452 | 452003 | 기말두수 | 3 | nan | 3.0 |
| 452 | 452004 | 상시 사육두수 | 4 | nan | 4.0 |
| 452 | 452005 | 총 전입두수 | 5 | nan | 5.0 |
| 452 | 452006 | 폐사두수 | 6 | nan | 6.0 |
| 452 | 452007 | 기초체중 | 7 | nan | 7.0 |
| 452 | 452008 | 분양/출하/전출두수 | 8 | nan | 8.0 |
| 452 | 452009 | 분양/출하/전출체중 | 9 | nan | 9.0 |
| 452 | 452010 | 기말체중 | 10 | nan | 10.0 |
| 452 | 452011 | 총 출하금액 | 11 | nan | 11.0 |
| 452 | 452012 | 총 사료입고량 | 12 | nan | 12.0 |
| 452 | 452018 | 총 이동전입체중 | 12 | nan | 12.0 |
| 452 | 452013 | 비육돈 사료요구율 | 13 | nan | 13.0 |
| 452 | 452019 | 평균 이동전입체중 | 13 | nan | 13.0 |
| 452 | 452014 | 총 사료비용 | 14 | nan | 14.0 |
| 452 | 452020 | 평균 전입일령 | 14 | nan | 14.0 |
| 452 | 452015 | Kg증체당 사료비 | 15 | nan | 15.0 |
| 452 | 452021 | 총 도폐사체중 | 15 | nan | 15.0 |
| 452 | 452016 | 상시두수대비 육성율 | 16 | nan | 16.0 |
| 452 | 452022 | 평균 도폐사체중 | 16 | nan | 16.0 |
| 452 | 452017 | 전입두수대비 육성율 | 17 | nan | 17.0 |
| 452 | 452023 | 출하/전출체중 | 17 | nan | 17.0 |
| 452 | 452024 | 총 출하두수 | 18 | nan | 18.0 |
| 452 | 452025 | 총 출하체중 | 19 | nan | 19.0 |
| 452 | 452026 | 평균 출하체중 | 20 | nan | 20.0 |
| 452 | 452027 | 규격돈 출하두수 | 21 | nan | 21.0 |
| 452 | 452028 | 위축돈 출하두수 | 22 | nan | 22.0 |
| 452 | 452029 | 총 종돈 출하두수 | 23 | nan | 23.0 |
| 452 | 452030 | 총 종돈 출하체중 | 24 | nan | 24.0 |
| 452 | 452031 | 평균 종돈 출하체중 | 25 | nan | 25.0 |
| 452 | 452032 | 총 전출두수 | 26 | nan | 26.0 |
| 452 | 452033 | 총 전출체중 | 27 | nan | 27.0 |
| 452 | 452034 | 평균 전출체중 | 28 | nan | 28.0 |
| 452 | 452035 | 증체중 | 29 | nan | 29.0 |
| 452 | 452036 | 총 사육일수 | 30 | nan | 30.0 |
| 452 | 452037 | 회전율 | 31 | nan | 31.0 |
| 452 | 452038 | 일당 증체중 | 32 | nan | 32.0 |
| 452 | 452039 | 일일 사료급여량 | 34 | nan | 34.0 |
| 452 | 452040 | 두당 일일사료급여량 | 35 | nan | 35.0 |
| 452 | 452041 | 사료 요구율 | 36 | nan | 36.0 |
| 452 | 452042 | 두당 사료비 | 39 | nan | 39.0 |
| 452 | 452043 | 평균 출하일령 | 40 | nan | 40.0 |
| 46 | 461 | 요일 | nan | nan | 0.0 |
| 461 | 461001 | 일 | 1 | nan | 10.0 |
| 461 | 461002 | 월 | 2 | nan | 20.0 |
| 461 | 461003 | 화 | 3 | nan | 30.0 |
| 461 | 461004 | 수 | 4 | nan | 40.0 |
| 461 | 461005 | 목 | 5 | nan | 50.0 |
| 461 | 461006 | 금 | 6 | nan | 60.0 |
| 461 | 461007 | 토 | 7 | nan | 70.0 |
| 47 | 471 | 그룹 일령산출 기준 | nan | nan | 0.0 |
| 47 | 472 | 비육돈 관리유형 | nan | nan | 0.0 |
| 471 | 471002 | 그룹기준 일령 | nan | nan | 100.0 |
| 471 | 471001 | 전입기준 일령(산술 평균) | nan | nan | 200.0 |
| 471 | 471003 | 전입기준 일령(가중치 평균) | nan | nan | 300.0 |
| 472 | 472001 | 그룹기준으로 관리 | nan | nan | 100.0 |
| 472 | 472002 | 돈사돈방 기준으로 관리 | nan | nan | 200.0 |
| 48 | 481 | 관리대상 구분정보 | nan | nan | 0.0 |
| 48 | 482 | 연통계 항목 정보 | nan | nan | 2.0 |
| 481 | 481001 | 관리-교배후분만지연돈 | nan | nan | 0.0 |
| 481 | 481002 | 관리-미교배 후보돈 | nan | nan | 0.0 |
| 481 | 481003 | 관리-분만후이유지연돈 | nan | nan | 0.0 |
| 481 | 481004 | 관리-사고후미교배돈 | nan | nan | 0.0 |
| 481 | 481005 | 관리-이유후미교배돈 | nan | nan | 0.0 |
| 481 | 481006 | 관리-초발정 후보돈 | nan | nan | 0.0 |
| 481 | 481007 | 이상두수-포유/이유 모돈수 | nan | nan | 0.0 |
| 482 | 482001 | 분만율 | BUNMAN | nan | 1.0 |
| 482 | 482002 | 평균 총산두수 | CHONGSAN | nan | 2.0 |
| 482 | 482003 | 도태두수 | DOTAE | nan | 3.0 |
| 482 | 482004 | 평균 이유두수 | EUDUSU | nan | 4.0 |
| 482 | 482005 | 모돈수 | MODON | nan | 5.0 |
| 482 | 482006 | 평균 실산 | SILSAN | nan | 6.0 |
| 482 | 482007 | 수태율 | SUTAE | nan | 7.0 |
| 482 | 482008 | 평균 재귀일 | ZAEGI | nan | 8.0 |
| 482 | 482009 | 7일내 재귀율 | ZAEGI7 | nan | 9.0 |
| 90 | 901 | 시스템 기능 분류 | nan | nan | 0.0 |
| 90 | 903 | 서비스 공개대상 | nan | nan | 0.0 |
| 90 | 907 | 요금측정기준 | nan | nan | 0.0 |
| 90 | 909 | 서비스구분 | nan | nan | 0.0 |
| 90 | 910 | 다중관리 계층레벨 | nan | nan | 0.0 |
| 90 | 904 | 업체소속메뉴 | nan | nan | nan |
| 90 | 906 | 항목구분 | nan | nan | nan |
| 901 | 901002 | 농가용 기능(WEB) | P | nan | 1.0 |
| 901 | 901003 | 업체용 기능(WEB) | U | nan | 2.0 |
| 901 | 901004 | 모바일 기능 | M | nan | 3.0 |
| 901 | 901001 | 관리자 기능 | S | nan | 99.0 |
| 901 | 901999 | 메인 | nan | nan | nan |
| 902 | 902006 | 도드람 농가서비스 | nan | nan | 0.0 |
| 902 | 902007 | 도드람 업체서비스 | nan | nan | 0.0 |
| 902 | 902008 | 돈돈팜 농가서비스 | nan | nan | 0.0 |
| 902 | 902009 | 돈돈팜 업체서비스 | nan | nan | 0.0 |
| 903 | 903001 | 서비스신청 | nan | nan | 0.0 |
| 903 | 903999 | 비공개 | nan | nan | 0.0 |
| 904 | 904001 | 도드람 | 15 | nan | nan |
| 904 | 904002 | 돈돈팜 | nan | nan | nan |
| 906 | 906010 | 서비스명 | svc | nan | 0.0 |
| 906 | 906001 | 항목 | itm | nan | nan |
| 906 | 906002 | 버튼 | btn | nan | nan |
| 906 | 906003 | 메세지 | msg | nan | nan |
| 906 | 906004 | 헬프메세지 | msghelp | nan | nan |
| 906 | 906005 | 라벨 | lba | nan | nan |
| 906 | 906006 | 타이틀명 | tit | nan | nan |
| 906 | 906007 | 메뉴 | mun | nan | nan |
| 906 | 906008 | 보고서 | rpt | nan | nan |
| 906 | 906009 | 데이터 값 | val | nan | nan |
| 907 | 907001 | 모돈 | nan | nan | 100.0 |
| 907 | 907002 | 종돈 | nan | nan | 200.0 |
| 907 | 907003 | 종돈(AI) | nan | nan | 250.0 |
| 907 | 907010 | 서비스단위 | nan | nan | 300.0 |
| 907 | 907020 | 농가단위 | nan | nan | 400.0 |
| 907 | 907999 | 무료 | nan | nan | 1000.0 |
| 909 | 909001 | 생산&업무관리 서비스 | nan | nan | 100.0 |
| 909 | 909004 | 종돈장 서비스 | nan | nan | 200.0 |
| 909 | 909002 | 다중관리&기업용 서비스 | nan | nan | 300.0 |
| 909 | 909003 | 빅데이터 분석 서비스 | nan | nan | 400.0 |
| 909 | 909006 | 모바일서비스 | nan | nan | 500.0 |
| 909 | 909005 | 기타 서비스 | nan | nan | 1000.0 |
| 91 | 913 | 농가/업체구분 | nan | nan | 0.0 |
| 91 | 914 | 비밀번호 힌트 | nan | nan | 0.0 |
| 91 | 915 | 시스템 사용처 | nan | nan | 0.0 |
| 91 | 916 | 필드타입 | nan | nan | 0.0 |
| 91 | 911 | 사용자 회원구분 | nan | nan | nan |
| 91 | 912 | 이지팜 회원구분 | nan | nan | nan |
| 910 | 910001 | 1 계층 구조 | nan | nan | 0.0 |
| 910 | 910002 | 2 계층 구조 | nan | nan | 0.0 |
| 910 | 910003 | 3 계층 구조 | nan | nan | 0.0 |
| 910 | 910004 | 4 계층 구조 | nan | nan | 0.0 |
| 911 | 911009 | 업체공통 | 913001 | 901003 | 0.0 |


### TC_CODE_JOHAP (ko)


| pcode | code | cname |
| --- | --- | --- |
| * | 01 | 지역 |
| * | 02 | 그룹 |
| * | 03 | 도폐사원인 |
| * | 04 | 품종 |
| * | 05 | 양자원인 |
| * | 06 | 질병 |
| * | 07 | 공통거래처 |
| * | 08 | 돈사종류 |
| * | 09 | 돈사형태 |
| * | 10 | 바닥형태 |
| * | 11 | 분뇨처리 |
| * | 13 | 단열형태 |
| * | 14 | 급수방식 |
| * | 15 | 사료급이방식 |
| * | 16 | 소독방법 |
| * | 17 | 등급 |
| * | 18 | 모돈규모 |
| * | 19 | 은행명 |
| * | 20 | 약품분류 |
| * | 21 | 소모품분류 |
| * | 22 | 보조재료분류 |
| * | 23 | 가계 |
| * | 24 | 이자율구분 |
| * | 25 | 접수방법 |
| * | 26 | 크레임사유 |
| * | 27 | 크레임처리방법 |
| * | 28 | 크레임확인방법 |
| * | 29 | bcs구분 |
| * | 30 | 질병치료방법 |
| * | 31 | 제품단위 |
| * | 32 | 전출처리상태 |
| * | 33 | 계열전출 크레임사유 |
| * | 34 | 출고구분 |
| * | 35 | 센서구분 |
| * | 36 | HACCP 후보돈 도입관리 구분 |
| * | 58 | 희석제명 |
| * | 64 | 적부판정구분 |
| * | 65 | 주기구분 |
| * | 70 | HACCP구분 |
| * | 71 | SMS사용자종류 |
| * | 72 | 통신사종류 |
| * | 73 | 센서지표종류 |
| * | 74 | 센서지표 돈종류 |
| * | 75 | HACCP후보돈도입검사평가구분 |
| * | 76 | 환경생산성적보고서 |
| * | 77 | 규격돈 도축등급 |
| * | 78 | 규격돈 도축판정구분 |
| * | 79 | 규격돈 도축등급 판정기준 |
| * | 80 | 규격돈_육색 |
| * | 81 | 규격돈정액 |
| * | 82 | PSS |
| * | 83 | PRRSV 농장기본정보 |
| * | 84 | 급이기 업체 정보 |
| 001 | 001 | test |
| 01 | 010001 | 서울경기 |
| 01 | 010002 | 충청남도 |
| 01 | 010003 | 충청북도 |
| 01 | 010004 | 전라남도 |
| 01 | 010005 | 전라북도 |
| 01 | 010006 | 경상남도 |
| 01 | 010007 | 경상북도 |
| 01 | 010008 | 강원도 |
| 01 | 010009 | 제주도 |
| 02 | 020001 | A |
| 02 | 020002 | B |
| 02 | 020003 | C |
| 02 | 020004 | D |
| 02 | 020005 | E |
| 02 | 020006 | F |
| 02 | 020007 | G |
| 02 | 020008 | H |
| 02 | 020009 | I |
| 02 | 020010 | J |
| 02 | 020012 | K |
| 02 | 020013 | L |
| 02 | 020014 | M |
| 02 | 020015 | N |
| 02 | 020016 | O |
| 02 | 020017 | P |
| 02 | 020018 | Q |
| 02 | 020019 | R |
| 02 | 020020 | S |
| 02 | 020021 | T |
| 02 | 020022 | U |
| 02 | 020023 | V |
| 02 | 020024 | W |
| 02 | 020025 | X |
| 02 | 020026 | Y |
| 02 | 020027 | Z |
| 02 | 020028 | 고창 |
| 03 | 031 | 종돈 |
| 03 | 032 | 포유자돈 |
| 03 | 033 | 폐사 |
| 031 | 031001 | 모름 |
| 031 | 031002 | 노산 |
| 031 | 031003 | 무발정 |
| 031 | 031004 | 재발다수 |
| 031 | 031005 | 자궁염증 |
| 031 | 031006 | 질병 |
| 031 | 031007 | 유산 |
| 031 | 031008 | 성적불량 |
| 031 | 031009 | 호흡기 |
| 031 | 031010 | 위축 |
| 031 | 031011 | 부종병 |
| 031 | 031012 | 지제불량 |
| 031 | 031013 | 압사 |
| 031 | 031014 | 후구마비 |
| 031 | 031015 | 소화기 |
| 031 | 031016 | 번식장애 |
| 031 | 031017 | 기타 |
| 031 | 031018 | 폐사 |
| 031 | 031019 | 판매 |
| 031 | 031020 | 노산돈 |
| 031 | 031021 | 불임 |
| 031 | 031022 | 무유증 |
| 031 | 031023 | 유두불량 |
| 031 | 031024 | 지제사고 |
| 031 | 031025 | 폐혈증 |
| 031 | 031026 | 원인불명(급사) |
| 031 | 031027 | 잦은재발 |
| 031 | 031028 | 자궁내막염 |
| 031 | 031029 | 산자수적음 |
| 031 | 031030 | 급사 |
| 031 | 031031 | 임신돈판매 |
| 031 | 031032 | 이유모돈판매 |
| 031 | 031033 | 가성광견병/오제스키 |
| 031 | 031034 | 감전사 |
| 031 | 031035 | 허약/영양부족/식불 |
| 031 | 031036 | 거식증 |
| 031 | 031037 | 검사 및 도태 |
| 031 | 031038 | 고령/노산 |
| 031 | 031039 | 골다공증 |
| 031 | 031040 | 관리소홀 |
| 031 | 031041 | 관절염 |
| 031 | 031042 | 관절염/안질 |
| 031 | 031043 | 구제역 |
| 031 | 031044 | 궤양 |
| 031 | 031045 | 근육골격이상 |
| 031 | 031046 | 글래서병 |
| 031 | 031047 | 급성설사 |
| 031 | 031048 | 급성심부전증 |
| 031 | 031049 | 급성유방염 |
| 031 | 031050 | 급성폐렴 |
| 031 | 031051 | 기립불능 |
| 031 | 031052 | 기타중독 |
| 031 | 031053 | 분만사고/난산 |
| 031 | 031054 | 내막염 |
| 031 | 031055 | 내부기생충 |
| 031 | 031056 | 농양 |
| 031 | 031057 | 뇌막염 |
| 031 | 031058 | 다발성장막염 |
| 031 | 031059 | 대사성질병 |
| 031 | 031060 | 대장균증 |
| 031 | 031061 | 돈군재편성 |
| 031 | 031062 | 돈단독 |
| 031 | 031063 | 돈적리 |
| 031 | 031064 | 동복질병 |
| 031 | 031065 | 돼지콜레라 |
| 031 | 031066 | 두부이상/이염 |
| 031 | 031067 | 렙토스피라감염증 |
| 031 | 031068 | 마이코플라스마폐렴 |
| 031 | 031069 | 만성설사 |
| 031 | 031070 | 만성옴(피부병) |
| 031 | 031071 | 만성유방염 |
| 031 | 031072 | 만성폐렴 |
| 031 | 031073 | 모돈번식장애 |
| 031 | 031074 | 무력증 |
| 031 | 031075 | 미임 |
| 031 | 031076 | 산자수저하 |
| 031 | 031077 | 변비 |
| 031 | 031078 | 복막염 |
| 031 | 031079 | 복합적이상 |
| 031 | 031080 | 부전각화증증/아연결핍 |
| 031 | 031081 | 분만성적저하 |
| 031 | 031082 | 분만실패 |
| 031 | 031083 | 불안정/야만 |
| 031 | 031084 | 브루셀라감염증 |
| 031 | 031085 | 비뇨기감염증 |
| 031 | 031086 | 비뇨생식기이상 |
| 031 | 031087 | 비정상돈 |
| 031 | 031088 | 비타민 E-셀레늄결핍증 |
| 031 | 031089 | 사고 |
| 031 | 031090 | 사산 또는 미이라 |
| 031 | 031091 | 산자수 |
| 031 | 031092 | 살모넬라감염증 |
| 031 | 031093 | 삼출성표피염 |
| 031 | 031094 | 스트레스증후군 |
| 031 | 031095 | 시장상황 또는 세금 |
| 031 | 031096 | 식미증 |
| 031 | 031097 | 신체상태 |
| 031 | 031098 | 심외막염 |
| 031 | 031099 | 심장혈관이상 |
| 031 | 031100 | 아프리카돈열 |
| 031 | 031101 | 액티노바실러스감염 |
| 031 | 031102 | 연쇄상구균감염증 |
| 031 | 031103 | 열상 |
| 031 | 031104 | 염중독 |
| 031 | 031105 | 양양적요인 |
| 031 | 031106 | 외상 |
| 031 | 031107 | 외음부농(분비물) |
| 031 | 031108 | 우상성심내막염 |
| 031 | 031109 | 웅돈번식장애 |
| 031 | 031110 | 웅돈성욕저하 |
| 031 | 031111 | 위장관계통이상 |
| 031 | 031112 | 위축성비염 |
| 031 | 031113 | 유방외상 |
| 031 | 031114 | 유전적원인 |
| 031 | 031115 | 인플루엔자 |
| 031 | 031116 | 임신실패 |
| 031 | 031117 | 임신진단음성 |
| 031 | 031118 | 자궁탈 |
| 031 | 031119 | 장폐색 |
| 031 | 031120 | 전염성위장염(TGE) |
| 031 | 031121 | 중독,공팜이독소 |
| 031 | 031122 | 중추신경계이상 |
| 031 | 031123 | 증식성장염 |
| 031 | 031124 | 지제이상/기립불능 |
| 031 | 031125 | 직장탈 |
| 031 | 031126 | 질식사 |
| 031 | 031127 | 질탈 |
| 031 | 031128 | 청각/시각장애 |
| 031 | 031129 | 출혈 |
| 031 | 031130 | 출혈성장염 |
| 031 | 031131 | 카니발리즘 |
| 031 | 031132 | 코리네박테리움감염증 |
| 031 | 031133 | 크기 |
| 031 | 031134 | 탈장/파열 |
| 031 | 031135 | 후산정체 |
| 031 | 031136 | 파보감염증 |
| 031 | 031137 | 파스튜렐라감염 |
| 031 | 031138 | 패혈증, 내부종양 |
| 031 | 031139 | 포유성적저하 |
| 031 | 031140 | 피부감염 |
| 031 | 031141 | 피부궤양 |
| 031 | 031142 | 피부병 |
| 031 | 031143 | 항문폐쇄 |
| 031 | 031144 | 행동이상 |
| 031 | 031145 | 허약돈 |
| 031 | 031146 | 헤모필루스속감염증 |
| 031 | 031147 | 호흡곤란 |
| 031 | 031148 | 흉막염 |
| 031 | 031149 | 자궁염 |
| 031 | 031150 | 폐렴 |
| 031 | 031151 | 관절이상(관절염) |
| 031 | 031152 | 열사병 |
| 031 | 031153 | 연속재발 |
| 031 | 031154 | 연속유산 |
| 031 | 031155 | 허약 |
| 031 | 031156 | 식불 |
| 031 | 031157 | 영양적요인 |
| 031 | 031158 | 중독, 곰팡이독소 |
| 031 | 031160 | 오제스키 |
| 031 | 031161 | 무정자 |
| 031 | 031162 | 승가불가 |
| 031 | 031163 | 재발 |
| 031 | 031164 | 급체 |
| 031 | 031165 | 재발/공태/불임 |
| 031 | 031166 | 탈항 |
| 031 | 031167 | 순종사분리 |
| 031 | 031168 | 탈창 |
| 031 | 031169 | 식체 |
| 031 | 031170 | 방광염 |
| 031 | 031171 | 저 산자수 |
| 031 | 031172 | 유방염 |
| 031 | 031173 | 종돈감축 |
| 031 | 031174 | 노산도태 |
| 031 | 031175 | 불임돈 도태 |
| 031 | 031176 | 재발돈 |
| 031 | 031177 | AR감염돈 |
| 031 | 031178 | 안락사 |
| 031 | 031179 | 분만장애,난산 |
| 031 | 031180 | 기립불 |
| 031 | 031181 | 임신장애 |
| 031 | 031182 | 만삭유산 |
| 031 | 031183 | 도태 |
| 031 | 031184 | 심한체손실(깡마름) |
| 031 | 031185 | 재발정 |
| 031 | 031186 | 공태 |
| 031 | 031187 | 유량불량 |
| 031 | 031188 | 호흡기질병문제 |
| 031 | 031189 | 기타질병문제 |
| 031 | 031190 | 일반판매 |
| 031 | 031191 | 이유두수불량 |
| 031 | 031192 | 식자(자돈물어죽임) |
| 031 | 031193 | 과건/과비 |
| 031 | 031194 | 자궁농 |
| 031 | 031195 | 신경증상 |
| 031 | 031196 | 고열 |
| 032 | 032001 | 압사 |
| 032 | 032002 | 설사 |
| 032 | 032003 | 기아 |
| 032 | 032004 | 기형 |
| 032 | 032005 | 허약 |
| 032 | 032006 | 원인불명(미상) |
| 032 | 032007 | 질병 |
| 032 | 032008 | 동사 |
| 032 | 032009 | 콕시듐 |
| 032 | 032010 | 포유중도태(임의) |
| 032 | 032011 | 식자 |
| 032 | 032012 | 체중미달 |
| 032 | 032013 | 관절이상 |
| 032 | 032014 | 급사 |
| 032 | 032015 | 창상 |
| 032 | 032016 | 위축 |
| 032 | 032017 | 쇄항(항문막힘) |
| 032 | 032018 | 견좌 |
| 032 | 032019 | 탈장 |
| 032 | 032020 | 진전(떨림) |
| 032 | 032021 | 고창증 |
| 032 | 032022 | 피부병 |
| 032 | 032099 | 기타 |
| 033 | 033001 | 기타(원인불명) |
| 033 | 033002 | 기아 |
| 033 | 033003 | 흉막폐렴 |
| 033 | 033004 | 위궤양 |
| 033 | 033005 | 대장균증 |
| 033 | 033006 | 장폐색 |
| 033 | 033007 | 직장탈(파열) |
| 033 | 033008 | 근육골격이상 |
| 033 | 033009 | 근진전증 |
| 033 | 033010 | 영양적요인(기아 등) |
| 033 | 033011 | 식미증 |
| 033 | 033012 | 급성폐렴 |
| 033 | 033013 | 피부병 |
| 033 | 033014 | 원인불명(급사) |
| 033 | 033015 | 압사 |
| 033 | 033016 | 비뇨생식기이상 |
| 033 | 033017 | PED |
| 033 | 033018 | TGE |
| 033 | 033019 | 콕시듐증 |
| 033 | 033020 | 회장염 |
| 033 | 033021 | 살모넬라증 |
| 033 | 033022 | 사고 |
| 033 | 033023 | 헤르니아 |
| 033 | 033024 | 신경장애 |
| 033 | 033025 | 임의도태 |
| 033 | 033026 | 판매 |
| 033 | 033027 | 로타 |
| 033 | 033028 | 관절 |
| 033 | 033029 | 위축 |
| 033 | 033030 | 돈적리 |
| 033 | 033031 | 마비 |
| 033 | 033032 | 투쟁 |
| 04 | 041 | 모돈 |
| 04 | 042 | 웅돈 |
| 04 | 043 | 비육돈 |
| 04 | 12 | 양자원인1 |
| 041 | 041001 | PP |
| 041 | 041002 | LD |
| 041 | 041003 | 테스트 |
| 041 | 041004 | LL |
| 041 | 041005 | LQ |
| 041 | 041006 | LY |
| 041 | 041007 | XX |
| 041 | 041008 | YF |
| 041 | 041009 | YL |
| 041 | 041010 | YY |
| 041 | 041011 | YH |
| 041 | 041012 | LA |
| 041 | 041013 | F1 |
| 041 | 041014 | AAA |
| 041 | 041015 | BBB |
| 041 | 041016 | CCC |
| 041 | 041017 | DDD |
| 041 | 041018 | L |
| 041 | 041019 | F2 |
| 041 | 041020 | F3 |
| 041 | 041021 | HH |
| 041 | 041022 | YB |
| 041 | 041023 | BB |
| 041 | 041024 | UN |
| 041 | 041025 | YD |
| 041 | 041027 | PT |
| 041 | 041028 | PI |
| 041 | 041029 | YLL |
| 041 | 041030 | LYL |
| 041 | 041031 | YLY |
| 041 | 041032 | LYY |
| 041 | 041033 | DD |
| 041 | 041034 | PC |
| 041 | 041035 | YLD |
| 041 | 041036 | DH |
| 041 | 041037 | T |
| 041 | 041038 | CB |
| 041 | 041039 | CC |
| 041 | 041040 | DB |
| 041 | 041041 | FB |
| 041 | 041042 | DA |
| 041 | 041043 | HA |
| 041 | 041044 | LB |
| 041 | 041045 | YA |
| 041 | 041046 | LH |
| 041 | 041047 | LT |
| 041 | 041048 | WW |
| 041 | 041049 | AS |
| 041 | 041050 | LS |
| 041 | 041051 | BK |
| 041 | 041052 | SW |
| 041 | 041053 | GG |
| 041 | 041054 | NI |
| 041 | 041055 | SJ |
| 041 | 041056 | CA |
| 041 | 041057 | CN |
| 041 | 041058 | G |
| 041 | 041059 | MC |
| 041 | 041060 | MK |
| 041 | 041061 | MS |
| 041 | 041062 | GL |
| 041 | 041063 | HD |
| 041 | 041064 | LG |
| 041 | 041065 | LM |
| 041 | 041066 | AF |
| 041 | 041067 | YN |
| 041 | 041068 | DW |
| 041 | 041069 | HB |
| 041 | 041070 | HP |
| 041 | 041071 | DY |
| 041 | 041072 | PS |
| 041 | 041073 | PL |
| 041 | 041074 | LY2 |
| 041 | 041075 | MSD |
| 041 | 041076 | AM |
| 041 | 041077 | FL |
| 041 | 041078 | KNP |
| 041 | 041079 | DRX |
| 041 | 041080 | CL |
| 041 | 041081 | BY |
| 041 | 041082 | CX |
| 041 | 041083 | BL |
| 041 | 041084 | DRB |
| 041 | 041085 | BD |
| 041 | 041086 | BH |
| 041 | 041087 | CHM |
| 041 | 041088 | CS |
| 041 | 041089 | LYD |
| 041 | 041090 | F4 |
| 041 | 041091 | YW |
| 042 | 042001 | DD |
| 042 | 042002 | DH |
| 042 | 042003 | DW |
| 042 | 042004 | DY |
| 042 | 042005 | LL |
| 042 | 042006 | YY |
| 042 | 042007 | DL |
| 042 | 042008 | L |
| 042 | 042009 | Y |
| 042 | 042010 | XX |
| 042 | 042011 | DU |
| 042 | 042012 | YO |
| 042 | 042013 | LA |
| 042 | 042014 | BL-2 |
| 042 | 042015 | PIC |
| 042 | 042016 | B |
| 042 | 042017 | HD |
| 042 | 042018 | DR |
| 042 | 042019 | BE |
| 042 | 042020 | BB |
| 042 | 042021 | Da |
| 042 | 042022 | DB |
| 042 | 042023 | Dc |
| 042 | 042024 | Dk |
| 042 | 042025 | Dx |
| 042 | 042026 | D5 |
| 042 | 042027 | Ba |
| 042 | 042028 | Bb |
| 042 | 042029 | Bl |
| 042 | 042030 | Bk |
| 042 | 042031 | BC |
| 042 | 042032 | B.D |
| 042 | 042033 | HH |
| 042 | 042034 | BDB |
| 042 | 042035 | YB |
| 042 | 042036 | PI |
| 042 | 042037 | BD |
| 042 | 042038 | YD |
| 042 | 042039 | CB |
| 042 | 042040 | CC |
| 042 | 042041 | JD |
| 042 | 042042 | LY |
| 042 | 042043 | A |
| 042 | 042044 | AF |
| 042 | 042045 | LD |
| 042 | 042046 | YN |
| 042 | 042047 | WD |
| 042 | 042048 | MS |
| 042 | 042049 | YL |
| 042 | 042050 | SJ |
| 042 | 042051 | F1 |
| 042 | 042052 | KNP |
| 042 | 042053 | UN |
| 042 | 042054 | CX |
| 042 | 042055 | CN |
| 042 | 042056 | PL |
| 042 | 042057 | BH |
| 042 | 042058 | HB |
| 042 | 042059 | PP |
| 042 | 042060 | YA |
| 042 | 042061 | WW |
| 043 | 043001 | YLD |
| 043 | 043002 | LYD |
| 043 | 043003 | YLL |
| 043 | 043004 | LY |
| 043 | 043005 | YL |
| 043 | 043006 | LL |
| 043 | 043007 | YY |
| 043 | 043008 | DD |
| 043 | 043009 | F1 |
| 043 | 043010 | YBD |
| 043 | 043011 | BB |
| 043 | 043012 | YB |
| 043 | 043013 | YWD |
| 05 | 050001 | 산자수 |
| 05 | 050002 | 포유중단 |
| 05 | 050003 | 모돈폐사 |
| 05 | 050004 | 재포유모돈 |
| 05 | 050005 | 젖불량 |
| 05 | 050006 | 기타 |
| 05 | 050007 | 포유불능 |
| 05 | 050008 | 사고기록누락 |
| 06 | 060001 | 돈열 |
| 06 | 060002 | PED |
| 06 | 060003 | 흉막폐렴 |
| 06 | 060004 | 기아 |
| 06 | 060005 | 위궤양 |
| 06 | 060006 | 대장균증 |
| 06 | 060007 | 장폐색 |
| 06 | 060008 | 직장탈(파열) |
| 06 | 060009 | 근육골격이상 |
| 06 | 060010 | 영양적요인 |
| 06 | 060011 | 급성폐렴 |
| 06 | 060012 | 피부병 |
| 06 | 060013 | 압사 |
| 06 | 060014 | 비뇨생식기이상 |
| 06 | 060015 | TGE |
| 06 | 060016 | 회장염 |
| 06 | 060017 | 살모넬라증 |
| 06 | 060018 | 헤르니아 |
| 06 | 060019 | 신경장애 |
| 06 | 060020 | 로타 |
| 06 | 060021 | 관절 |
| 06 | 060022 | 위축 |
| 06 | 060023 | 기타원인불명 |
| 06 | 060024 | 임의도태 |
| 07 | 071 | 종돈거래처 |
| 07 | 072 | 사료거래처 |
| 07 | 073 | 출하거래처 |
| 07 | 074 | 약품거래처 |
| 07 | 075 | 자돈거래처 |
| 07 | 076 | 기타거래처 |
| 071 | 071001 | 다비육종 |
| 071 | 071002 | 가야육종 |
| 071 | 071003 | 불명 |
| 072 | 072001 | 주사료회사 |
| 073 | 073001 | 안성공판 |
| 073 | 073002 | 부경공판 |
| 073 | 073003 | 개인상인 |
| 08 | 080001 | 후보돈사 |
| 08 | 080002 | 종부번식사 |
| 08 | 080003 | 임신사 |
| 08 | 080004 | 분만사 |
| 08 | 080005 | 자돈사 |
| 08 | 080006 | 육성사 |
| 08 | 080007 | 전기비육사 |
| 08 | 080008 | 베이비하우스 |
| 08 | 080009 | 후기비육사 |
| 08 | 080010 | 검정사 |
| 080001 | 080101 | 초교배일령 |
| 080001 | 080102 | 육성율 |
| 080002 | 080201 | 수태율 |
| 080002 | 080202 | 평균발정재귀율 |
| 080003 | 080301 | 임신사고율 |
| 080003 | 080302 | 임신사고재발율 |
| 080004 | 080401 | 분만율 |
| 080004 | 080402 | 총산 |
| 080004 | 080403 | 실산 |
| 080004 | 080404 | 이유전폐사율 |
| 080005 | 080501 | 육성율 |
| 080005 | 080502 | 사료효율 |
| 080005 | 080503 | 증체량 |
| 080010 | 081011 | 육성율 |
| 080010 | 081012 | 사료효율 |
| 080010 | 081013 | 증체량 |
| 09 | 090001 | 기계환기(무창) |
| 09 | 090002 | 자연+기계 |
| 09 | 090003 | 무창+윈치 |
| 09 | 090004 | 자연환기(개방) |
| 09 | 090005 | 하우스돈사 |
| 10 | 100001 | 전면슬랏 |
| 10 | 100002 | 부분슬랏 |
| 10 | 100003 | 평사 |
| 10 | 100004 | 톱밥 |
| 11 | 110001 | 슬러리 |
| 11 | 110002 | 스크레파 |
| 11 | 110003 | 톱밥 |
| 11 | 110004 | 인력수거 |
| 11 | 110005 | 기타 |
| 12 | 120001 | 자연환기 |
| 12 | 120002 | 혼합식 |
| 12 | 120003 | 양압 |
| 12 | 120004 | 중압 |
| 12 | 120005 | 음압 |
| 13 | 131 | 지붕 |
| 13 | 132 | 벽면 |
| 131 | 131001 | 우레탄 |
| 131 | 131002 | 슬레이트 |
| 131 | 131003 | 샌드위치판넬 |
| 131 | 131004 | +보온덮개 |
| 132 | 132001 | 슬레이트 |
| 132 | 132002 | 판자 |
| 132 | 132003 | 벽돌 |
| 132 | 132004 | 샌드위치판넬 |
| 132 | 132005 | 우레탄 |
| 132 | 132006 | 적벽돌 |
| 132 | 132007 | 갈바륨 |
| 132 | 132008 | 보온덮개 |
| 132 | 132009 | 전면윈치 |
| 132 | 132010 | 부분윈치 |
| 14 | 140001 | 자동급수 |
| 14 | 140002 | 수동급수 |
| 15 | 150001 | 자동급이 |
| 15 | 150002 | 수동급이 |
| 15 | 150003 | 테스트 |
| 16 | 160001 | 물세척 |
| 16 | 160002 | 자동세척 |
| 17 | 171 | 돈사등급 |
| 17 | 172 | 단열등급 |
| 171 | 171001 | A급 |
| 171 | 171002 | B급 |
| 171 | 171003 | C급 |
| 171 | 171004 | D급 |
| 171 | 171005 | E급 |
| 172 | 172001 | A급 |
| 172 | 172002 | B급 |
| 172 | 172003 | C급 |
| 172 | 172004 | D급 |
| 172 | 172005 | E급 |
| 18 | 180001 | 100두미만 |
| 18 | 180002 | 100~200두 |
| 18 | 180003 | 200~300두 |
| 18 | 180004 | 300~400두 |
| 18 | 180005 | 400~500두 |
| 18 | 180006 | 500~1000두 |
| 18 | 180007 | 1000두이상 |
| 18 | ALL | 전체 |
| 19 | 190001 | 농협 |
| 19 | 190002 | 우체국 |
| 19 | 190003 | 국민은행 |
| 19 | 190004 | 제일은행 |
| 19 | 190005 | 하나은행 |
| 19 | 190006 | 사무실 |
| 20 | 200001 | 백신류 |
| 20 | 200002 | 호르몬 |
| 20 | 200003 | 영양제 |
| 20 | 200004 | 구충제 |
| 20 | 200005 | 면역증강제 |
| 20 | 200006 | 소염제 |
| 20 | 200007 | 치료제 |
| 20 | 200008 | 항생제 |
| 20 | 200009 | 첨가제 |
| 20 | 200010 | 소독제 |
| 20 | 200011 | 살서제 |
| 20 | 200012 | 희석제 |
| 20 | 200013 | 구서제 |
| 20 | 200014 | 기타 |
| 21 | 210001 | 주사기 |
| 21 | 210002 | 주사침 |
| 21 | 210003 | 메스 |
| 21 | 210004 | 의류복 |
| 21 | 210005 | 약품류 |
| 21 | 210006 | 소독기 |
| 21 | 210007 | 기타 |
| 22 | 220001 | 사료보조재료 |
| 22 | 220002 | 방역보조재료 |
| 23 | 230001 | A |
| 23 | 230002 | B |
| 23 | 230003 | C |
| 23 | 230004 | D |
| 23 | 230005 | E |
| 23 | 230006 | F |
| 23 | 230007 | R |
| 23 | 230008 | Y |
| 23 | 230009 | W |
| 23 | 230010 | G |
| 24 | 240001 | 지연이자 |
| 24 | 240002 | 연체이자율 |
| 25 | 250001 | 전화접수 |
| 25 | 250002 | 방문접수 |
| 25 | 250003 | 이메일접수 |
| 26 | 260001 | 설사 |
| 26 | 260002 | 무발정 |
| 26 | 260003 | 호흡기질환 |
| 26 | 260004 | 폐사 |
| 26 | 260005 | 유두불량 |
| 26 | 260006 | 골절 |
| 26 | 260007 | 지제불량 |
| 26 | 260008 | 외음부왜소 |
| 26 | 260009 | 탈항 |
| 26 | 260010 | 승가불능 |
| 26 | 260011 | 페니스기형 |
| 26 | 260012 | 기타 |
| 26 | 260013 | 기타(자궁농) |
| 26 | 260014 | 위축 |
| 27 | 270001 | 미처리 |
| 27 | 270002 | 교환 |
| 27 | 270003 | 상담 |
| 27 | 270004 | 크레임처리 |
| 28 | 280001 | 미처리 |
| 28 | 280002 | 농가방문 |
| 28 | 280003 | 사진 |
| 28 | 280004 | E_MAIL |
| 28 | 280005 | 전화상담 |
| 29 | 290001 | 교배후 50일 |
| 29 | 290002 | 분만전 |
| 29 | 290003 | 이유시기 |
| 30 | 300001 | 개별주사 |
| 30 | 300002 | 사료희석 |
| 30 | 300003 | 물희석 |
| 31 | 310001 | 병 |
| 31 | 310002 | 팩 |
| 31 | 310003 | BOX |
| 31 | 310004 | 봉지 |
| 31 | 310005 | 개 |
| 31 | 310006 | 포 |
| 31 | 310007 | 통 |
| 31 | 310008 | Set |
| 31 | 310009 | Ea |
| 31 | 310010 | 벌 |
| 31 | 310011 | 켤레 |
| 31 | 310012 | bot |
| 31 | 310013 | 대 |
| 31 | 310014 | 매 |
| 31 | 310015 | 리터 |
| 31 | 310016 | kg |
| 31 | 310017 | g |
| 31 | 310018 | ml |
| 32 | 320001 | 전출 확인 |
| 32 | 320002 | 전입 확인 |
| 32 | 320003 | 전출 완료 |
| 32 | 320004 | 전입 완료 |
| 32 | 320005 | 출하등록 |
| 32 | 320006 | 출하승인 |
| 32 | 320007 | 외부전출 |
| 32 | 320008 | 외부출하 |
| 32 | 320009 | 반송 |
| 32 | 320010 | 외부출하승인 |
| 32 | 320011 | 철회 |
| 33 | 330001 | 골절 |
| 33 | 330002 | 설사 |
| 33 | 330003 | 호흡기질환 |
| 33 | 330004 | 위축 |
| 33 | 330005 | 기타사유 |
| 34 | 340001 | 정상출고 |
| 34 | 340002 | 파손 |
| 34 | 340003 | 유효기간초과 |
| 34 | 340004 | 재고조사정리 |
| 35 | 350001 | 환경센서 |
| 35 | 350002 | 온도 |
| 35 | 350003 | 이산화탄소 |
| 35 | 350004 | 습도 |
| 35 | 350005 | 사료빈 |
| 35 | 350006 | 음수기 |
| 35 | 350007 | 포유모돈급이기 |
| 35 | 350008 | 군사급이기 |
| 35 | 350009 | 자돈급이기 |
| 35 | 350010 | CCTV |
| 35 | 350011 | 암모니아 |
| 35 | 350012 | 환기 |
| 36 | 360001 | 후보모돈 |
| 36 | 360002 | 웅돈 |
| 36 | 360003 | 비고 |
| 58 | 580001 | 바이오피그 |
| 58 | 580002 | 프라임산 |
| 58 | 580003 | 나비젠알파 |
| 64 | 640001 | 적합,부적합 |
| 64 | 640002 | 점수 |
| 65 | 650001 | 년1회 |
| 65 | 650002 | 년2회 |
| 65 | 650003 | 년3회 |
| 65 | 650004 | 년4회 |
| 65 | 650005 | 월1회 |
| 65 | 650006 | 월2회 |
| 65 | 650007 | 월3회 |
| 65 | 650008 | 월4회 |
| 65 | 650009 | 주1회 |
| 65 | 650010 | 주2회 |
| 65 | 650011 | 주3회 |
| 65 | 650012 | 주4회 |
| 70 | 701 | 양돈사육농장 평가사항 |
| 701 | 701001 | 차단방역관리 |
| 701 | 701002 | 농장시설및관리기준 |
| 701 | 701003 | 농장위생관리 |
| 701 | 701004 | 사료,동물용의약품,음수관리등 |
| 701 | 701005 | 질병관리 |
| 701 | 701006 | 반입및출하관리 |
| 701 | 701007 | HACCP관리 |
| 71 | 710001 | 농장관리자 |
| 71 | 710002 | 돈사관리자 |
| 71 | 710003 | 사료운전기사 |
| 72 | 720001 | SKT |
| 72 | 720002 | KTF |


## E. 농장 식별 + 파일럿 4개 농장

### 상위 농장(모돈수) — TEST 제외


| farm_no | farm_nm | company_cd | modon_cnt |
| --- | --- | --- | --- |
| 1706 | 결성농장 | 15 | 29463 |
| 2056 | 금오양돈 | 1 | 28875 |
| 2411 | 법현농장 | 6 | 25061 |
| 634 | 대덕농장 | 15 | 18100 |
| 1183 | 옥산영농조합법인 | 16 | 15842 |
| 1938 | 영암농장 | 7 | 15543 |
| 1073 | 은하양돈 | 6 | 14614 |
| 983 | 완주농장 | 7 | 14594 |
| 1006 | 신화축산 | 1 | 14133 |
| 2680 | 연수농장 | 6 | 13726 |
| 1763 | 만해농장 | 15 | 13040 |
| 1399 | 도화농장 | 14 | 12792 |
| 1829 | 지정농장 | 6 | 12386 |
| 2013 | 청림축산 | 15 | 12132 |
| 110 | (유)1태흥축산 | 54 | 11779 |
| 1412 | 대월청안 | 14 | 11253 |
| 1773 | 나눔1농장 | 15 | 11123 |
| 24 | (유)2태흥축산 | 54 | 10927 |
| 4794 | 엘디팜_2팀 | 61 | 10899 |
| 1743 | 거성축산(전북) | 15 | 10161 |
| 3986 | 마이피그팜 | 1 | 10049 |
| 4037 | 푸른FND | 36 | 9787 |
| 1983 | 대운축산 | 10 | 9645 |
| 1839 | 우리농장 | 1 | 8787 |
| 1401 | 디앤디농장 | 14 | 8744 |


### ★ 파일럿 4개 농장 데이터 충실도


| farm_no | farm_nm | modon | wk | bunman | gyobae | eu | sago |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 848 | 서해농장 | 7435 | 117196 | 33573 | 42076 | 33511 | 8036 |
| 978 | (유)무럭이농장 | 8411 | 90869 | 26916 | 32108 | 27098 | 4747 |
| 2807 | 용암축산 | 1416 | 22700 | 6101 | 8336 | 6279 | 1984 |
| 4448 | 민근농장/장일농장 | 663 | 7054 | 2101 | 2624 | 2055 | 274 |


## F. 테이블별 규모(COUNT)


| 테이블 | 행수 |
| --- | --- |
| TA_FARM | 3201 |
| TB_MODON | 3449986 |
| TB_UNGDON | 59737 |
| TB_MODON_WK | 42079388 |
| TB_GYOBAE | 15462523 |
| TB_BUNMAN | 11956346 |
| TB_EU | 11850575 |
| TB_SAGO | 2808793 |
| TB_MODON_JADON_TRANS | 10536123 |
| TG_BUN_JADON | 4763055 |
| TJ_GAIN_GRP | 152263 |
| TJ_DUSU_MNG | 2632176 |
| TC_FARM_COMP | 18268 |
| TC_FARM_CONFIG | 610914 |
| TM_ETC_TRADE | 2275645 |
