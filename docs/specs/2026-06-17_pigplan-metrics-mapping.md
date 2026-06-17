# PigPlan 146지표 ↔ PigOS 매핑 (R1)

> 출처(gold standard): `c:/dev/realtime/전체농가_품종별_주요생산성적_2025.xlsx`
> long-format `농가번호|농가명|품종코드|품종명|지표명|값`, **데이터행 159,349 / 품종(집계축) 5 / distinct 지표명 146**.
> 추출: `openpyxl` distinct 지표명(최초등장 순). 원본 목록 `docs/specs/_pigplan_metrics_raw.txt`.
> 작성일 2026-06-17. **수치 임의 생성 없음 — 매핑·분류만.** 불확실은 ③로 보수 표기.

## 분류 정의
- **① 이미 계산** — PigOS 엔드포인트/서비스/룰엔진에서 현재 산출(또는 직접 파생).
- **② 데이터 있음·미집계** — 이벤트 테이블에 원천 필드 존재, 집계 로직만 추가하면 산출 가능.
- **③ 데이터 부족** — 산출에 필요한 필드/이벤트가 현재 스키마에 없음(추가 입력 설계 필요).
- **국가차등 Y/N** — 기준값/임계/단위/정의가 국가별로 달라야 하는가(④축, R2에서 상세).

## 근거가 된 PigOS 현황 (요약)
- 보고서: `api/app/services/report_service.py` reproduction = {total_matings, total_farrowings, total_weanings, fr, avg_tb, avg_ba, avg_weaned, avg_lactation_days, pwmr_a, pwmr_b, rts_rate}; grow-finish = {adg_g, fcr, mortality_rate}.
- 룰엔진/스냅샷: PSY/NPD/FR/PWMR(A·B)/RTS/WSI (`engine/rules/*`, `kpi_snapshots`).
- 이벤트 필드: Mating(mating_type AI|NATURAL, mating_number 1~5, boar_id), PregnancyCheck(result, days_after_mating), Farrowing(total_born, born_alive, stillborn, mummified, farrowing_ease EASY|ASSISTED|DIFFICULT), Weaning(weaned_count, weaning_age_days, avg_weaning_weight_kg), ReproductiveEvent(RTS|ABORTION|EMPTY|INFERTILE|CULLED|DEAD|TRANSFER_OUT|SOLD|HEAT_DETECTED), PigletEvent(STILLBORN_REMOVAL|DEATH|FOSTER_IN|FOSTER_OUT, reason).
- **스키마 갭(중요)**: Farrowing에 **생시체중(birth weight) 컬럼 없음** → 생시체중 계열 전부 ③. 분만구분은 `farrowing_ease`(난이도 3종)만 있어 PigPlan 4구분(정상/조산/유도/사고난산)과 불일치 → ③. 보정21일령체중/재포유 입력 없음 → ③. 후보돈 사육일수·전입일령은 sow.birth_date/entry_date 필요(부분).

---

## A. 모돈 재고·도폐사·전입출 (지표 1~21)

| # | 지표명(ko) | en | PigOS metric/source | 분류 | 계산식 또는 갭 | 국가차등 |
|---|-----------|----|--------------------|----|----------------|---------|
|1|상시모돈수|Avg sow inventory|sows(status≠CULLED/DEAD) 기간평균|②|일자별 재고 평균. 현재 미집계|N|
|2|후보돈포함상시모돈수|Avg inventory incl. gilts|sows incl GILT|②|위 + GILT 포함|N|
|3|기말재고모돈평균산차|End-stock avg parity|sows.parity 평균(기말)|②|breeding_cycles.parity 평균|N|
|4|도태모돈평균산차|Culled sow avg parity|ReproductiveEvent CULLED + parity|②|도태 시점 산차 평균|Y(도태 산차 정책차)|
|5|평균전입일령|Avg age at entry|sow.entry_date−birth_date|③|sow birth_date 확보 여부 불확실|N|
|6|기초모돈재고(후보제외)|Opening sow stock|sows 기초시점|②|기간시작 재고 스냅샷|N|
|7|기말모돈재고(후보제외)|Closing sow stock|sows 기말시점|②|기간종료 재고 스냅샷|N|
|8|모돈/웅돈비율|Sow:boar ratio|sows/boars count|②|boars 테이블 카운트비|N|
|9|모돈도태율|Sow culling rate|ReproductiveEvent CULLED/avg inv|②|도태두수/평균사육두수|Y|
|10|모돈폐사두수|Sow death count|ReproductiveEvent DEAD|②|count|N|
|11|연간모돈전입률|Annual replacement rate|전입두수/평균재고|②|전입(신규 sow)/avg inv|Y|
|12|모돈폐사율|Sow mortality rate|DEAD/avg inv|②|폐사두수/평균사육두수|Y|
|13|모돈도폐사율|Sow cull+death rate|(CULLED+DEAD)/avg inv|②|도폐사 합/평균재고|Y|
|14|모돈도태두수|Sow culled count|ReproductiveEvent CULLED|②|count|N|
|15|모돈전입두수|Sow entry count|sows 신규 entry|②|기간 내 신규 모돈|N|
|16|모돈판매두수|Sow sold count|ReproductiveEvent SOLD|②|count|N|
|17|모돈전출두수|Sow transfer-out|ReproductiveEvent TRANSFER_OUT|②|count|N|
|18|평균전입교배간격|Avg entry→1st mating gap|entry_date→첫 mating|③|sow.entry_date 신뢰도 불확실|Y(후보 초교배 관습차)|
|19|기초후보돈|Opening gilt stock|sows status=GILT 기초|②|기초 GILT 재고|N|
|20|기말후보돈|Closing gilt stock|sows status=GILT 기말|②|기말 GILT 재고|N|
|21|총도폐사판매모돈수|Total cull+death+sold|CULLED+DEAD+SOLD|②|합산|N|

## B. 교배 (지표 22~46)

| # | 지표명 | en | source | 분류 | 식/갭 | 국가차등 |
|---|--------|----|--------|----|-------|---------|
|22|교배복수|Total matings|Mating count = `total_matings`|①|보고서 total_matings|N|
|23|1회교배복수|1st-service matings|Mating.mating_number=1|②|count(mating_number=1)|N|
|24|2회교배복수|2nd-service matings|mating_number=2|②|count|N|
|25|3회교배복수|3rd-service matings|mating_number=3|②|count|N|
|26|1회교배복수비율|1st-service %|number=1/total|②|비율|N|
|27|3회이상교배비율|≥3 service %|number≥3/total|②|비율|N|
|28|순자연교배|Pure natural matings|mating_type=NATURAL(사이클내 단일)|②|cycle별 type 분해|N|
|29|순인공교배|Pure AI matings|mating_type=AI(사이클내 단일)|②|count|N|
|30|혼합교배|Mixed AI+natural|cycle에 AI&NATURAL 병존|②|cycle 그룹 후 판정|N|
|31|순자연교배비율|Pure natural %|위/total cycles|②|비율|N|
|32|순인공교배비율|Pure AI %|위/total cycles|②|비율|N|
|33|혼합교배비율|Mixed %|위/total cycles|②|비율|N|
|34|정상교배|Normal mating|mating_number=1 & 직전 사고 없음|②|이벤트 시퀀스로 분류|N|
|35|1차재발교배|1st return mating|RTS 후 재교배(1차)|②|ReproductiveEvent RTS + mating seq|N|
|36|2차재발교배|2nd return mating|RTS 2회 후 재교배|②|seq|N|
|37|기타사고후교배|Post-accident mating|ABORTION/EMPTY 후 재교배|②|event seq|N|
|38|미경산돈교배복수|Gilt matings|status=GILT 모돈 mating|②|GILT 필터 count|N|
|39|미경산정상교배|Gilt normal mating|GILT & number=1|②|count|N|
|40|미경산재발교배|Gilt return mating|GILT & RTS후|②|count|N|
|41|미경산기타사고후교배|Gilt post-accident|GILT & 사고후|②|count|N|
|42|경산돈정상교배|Parous normal mating|parity≥1 & number=1|②|count|N|
|43|경산돈재발교배|Parous return mating|parity≥1 & RTS후|②|count|N|
|44|경산돈기타사고후교배|Parous post-accident|parity≥1 & 사고후|②|count|N|
|45|초교배복수(모돈편입)|Gilt 1st-mating entries|GILT→교배 편입 건|②|GILT 첫 mating count|N|
|46|평균초교배일령|Avg age at 1st mating|첫 mating−birth_date|③|sow.birth_date 필요(불확실)|Y(후보 초교배일령 관습차 큼)|

## C. 재귀발정 (지표 47~60)

| # | 지표명 | en | source | 분류 | 식/갭 | 국가차등 |
|---|--------|----|--------|----|-------|---------|
|47|재귀발정계산교배모돈수|WSI denom (mated sows)|이유→재교배 모돈수|②|WSI 계산 분모|N|
|48|총재귀일수|Total WSI days|Σ(재교배일−이유일)|②|이유·교배 날짜차 합|N|
|49|평균재귀발정일령|Avg WSI days|총재귀일수/모돈수 = WSI|①|룰엔진 WSI 사용 중|Y(WSI 목표차)|
|50|3일내재귀복수|WSI ≤3d count|간격≤3|②|버킷 count|N|
|51|4일재귀복수|WSI=4d count|간격=4|②|count|N|
|52|5일재귀복수|WSI=5d count|간격=5|②|count|N|
|53|6일재귀복수|WSI=6d count|간격=6|②|count|N|
|54|7일재귀복수|WSI=7d count|간격=7|②|count|N|
|55|8일재귀복수|WSI=8d count|간격=8|②|count|N|
|56|9일재귀복수|WSI=9d count|간격=9|②|count|N|
|57|10일이상재귀복수|WSI≥10d count|간격≥10|②|count|N|
|58|7일내재귀율|WSI≤7d %|(≤7)/모돈수|②|비율|Y(목표 분포차)|
|59|4~6일재귀율|WSI 4–6d %|(4..6)/모돈수|②|비율|N|
|60|재발교배비율|Return-to-service %|RTS/total matings = `rts_rate`|①|보고서 rts_rate|Y|

## D. 임신·분만예정·임신사고 (지표 61~70)

| # | 지표명 | en | source | 분류 | 식/갭 | 국가차등 |
|---|--------|----|--------|----|-------|---------|
|61|분만예정복수|Expected farrowings|교배+114d 예정|②|gestation(farm_config)로 산정|N|
|62|임신사고1차재발|Preg-fail 1st return|RTS(1차) during gestation|②|event 분류|N|
|63|임신사고2차재발|Preg-fail 2nd return|RTS(2차)|②|count|N|
|64|임신사고기타재발|Preg-fail other return|ABORTION/EMPTY|②|count|N|
|65|유산(예정돈중)|Abortions (of expected)|ReproductiveEvent ABORTION|②|count|N|
|66|도태(예정돈중)|Culls (of expected)|CULLED during gestation|②|count|N|
|67|폐사(예정돈중)|Deaths (of expected)|DEAD during gestation|②|count|N|
|68|임돈전출(예정돈중)|Preg transfer-out|TRANSFER_OUT(임신중)|②|count|N|
|69|임돈판매(예정돈중)|Preg sold|SOLD(임신중)|②|count|N|
|70|분만예정돈임신사고복수|Preg-fail total|62~69 합|②|합산|N|

## E. 분만·산자수 (지표 71~101)

| # | 지표명 | en | source | 분류 | 식/갭 | 국가차등 |
|---|--------|----|--------|----|-------|---------|
|71|분만복수|Farrowings|Farrowing count = `total_farrowings`|①|보고서|N|
|72|분만율|Farrowing rate|farrowings/matings = `fr`|①|보고서 fr|Y(목표차)|
|73|보정분만율|Adjusted farrowing rate|FR 보정(전출·판매 제외)|②|분모 보정 로직 추가|Y|
|74|분만구분정상|Farrowing: normal|—|③|farrowing_ease(EASY/ASSISTED/DIFFICULT)는 4구분과 불일치|N|
|75|분만구분조산|Farrowing: premature|—|③|조산 구분 필드 없음|N|
|76|분만구분유도분만|Farrowing: induced|—|③|유도분만 플래그 없음|N|
|77|분만구분사고난산|Farrowing: dystocia|farrowing_ease=DIFFICULT 근사|③|정확 매핑 아님(근사만)|N|
|78|총산(총산자수)|Total born|Farrowing.total_born 합|①|보고서 avg_tb 기반|N|
|79|실산(생존산자수)|Born alive|born_alive 합|①|avg_ba 기반|N|
|80|미라|Mummified|mummified 합|②|count(현재 보고서 미노출)|N|
|81|사산|Stillborn|stillborn 합|②|count|N|
|82|미라분만모돈수|Sows w/ mummies|mummified>0 모돈수|②|count|N|
|83|사산분만모돈수|Sows w/ stillborn|stillborn>0 모돈수|②|count|N|
|84|평균총산|Avg total born|= `avg_tb`|①|보고서|Y(목표차)|
|85|평균실산(평균생존산자수)|Avg born alive|= `avg_ba`|①|보고서|Y|
|86|생시체중측정분만복수|Farrowings w/ birth wt|—|③|**생시체중 필드 없음**|N|
|87|생시체중측정실산자수|Born-alive w/ birth wt|—|③|동일|N|
|88|평균복당생시체중|Avg litter birth wt|—|③|동일|N|
|89|평균자돈당생시체중|Avg piglet birth wt|—|③|동일|Y(품종 기준차)|
|90|생시자돈사고율|Birth loss rate|(sb+mum)/tb|②|(사산+미라)/총산|N|
|91|사산율|Stillborn rate|sb/tb|②|비율|N|
|92|미라율|Mummified rate|mum/tb|②|비율|N|
|93|복당생시사고두수|Loss per litter|(sb+mum)/farrowings|②|비율|N|
|94|복당임신사고일수|Preg-fail days/litter|임신사고 일수/복수|③|사고일수 산정 정의 필요|N|
|95|수태율(46일까지)|Conception rate (46d)|PregnancyCheck POSITIVE≤46d/matings|②|임신감정 집계 추가|Y|
|96|분만모돈평균산차|Farrowed sow avg parity|cycle.parity 평균(분만)|②|평균|N|
|97|생시도태|Birth-time culls|PigletEvent(분만직후 도태)|③|분만시 도태 구분 필요|N|
|98|생시도태분만모돈수|Sows w/ birth culls|위 보유 모돈수|③|동일|N|
|99|이유모돈두수|Weaned sows|Weaning distinct sow|①|total_weanings 근사|N|
|100|이유복수(대리모포함)|Weanings (incl. nurse)|Weaning count = `total_weanings`|①|보고서|N|
|101|이유체중측정두수비율|% weighed at wean|avg_weaning_weight_kg 보유 비율|②|측정복/전체|N|

## F. 이유·자돈 (지표 102~120)

| # | 지표명 | en | source | 분류 | 식/갭 | 국가차등 |
|---|--------|----|--------|----|-------|---------|
|102|보정21일령체중|Adjusted 21d weight|—|③|21일 보정식+측정체중 필요|Y(품종/시장 기준차)|
|103|평균이유두수|Avg weaned/litter|= `avg_weaned`|①|보고서|Y(목표차)|
|104|평균이유일령(대리모제외)|Avg weaning age|Weaning.weaning_age_days 평균|②|대리모 제외 필터 추가|Y(이유일령 관습/복지 규정차 큼)|
|105|평균자돈당이유체중|Avg piglet wean wt|Weaning.avg_weaning_weight_kg|②|평균(현 미노출)|Y|
|106|평균복당이유체중|Avg litter wean wt|avg_weaning_weight×weaned|②|파생|N|
|107|이유모돈실산자수|Weaned sows' born-alive|이유모돈의 ba 합|②|조인 집계|N|
|108|양자두수|Fostered piglets|PigletEvent FOSTER_IN/OUT|②|count|N|
|109|보정21일체중측정복수|Litters w/ 21d wt|—|③|보정체중 미측정|N|
|110|이유체중측정이유복수|Weanings w/ wt|avg_weaning_weight_kg not null|②|count|N|
|111|재포유모돈두수|Re-nursing sows|—|③|재포유 이벤트 없음|N|
|112|이유체중측정이유자돈수|Weaned piglets w/ wt|측정 weaning의 weaned 합|②|합|N|
|113|이유전폐사율(기간중)|Pre-wean mortality(period)|PWMR method A = `pwmr_a`|①|보고서|Y|
|114|총보정21일령체중|Total adj 21d weight|—|③|보정체중 미측정|N|
|115|총이유일령|Total weaning age-days|Σ weaning_age_days|②|합|N|
|116|총재포유자돈수|Total re-nursed piglets|—|③|재포유 미입력|N|
|117|총입력자돈폐사두수|Total piglet deaths|PigletEvent DEATH 합|①|보고서 deaths 사용|N|
|118|총이유자돈수|Total weaned piglets|Σ weaned_count|①|보고서|N|
|119|총이유자돈수(부분이유포함)|Total weaned (incl partial)|부분이유 포함 합|③|부분이유 구분 필드 없음|N|
|120|이유전폐사율(실산대비이유)|PWMR (BA vs weaned)|PWMR method B = `pwmr_b`|①|보고서|Y|

## G. 임신·포유기간·분만간격·NPD·회전율·PSY/MSY (지표 121~146)

| # | 지표명 | en | source | 분류 | 식/갭 | 국가차등 |
|---|--------|----|--------|----|-------|---------|
|121|총임신기간|Total gestation days|Σ(분만−교배)|②|합|N|
|122|평균임신기간|Avg gestation days|총/분만복수|②|평균|N|
|123|총포유기간|Total lactation days|Σ weaning_age_days(=lact)|②|합(보고서 avg만)|N|
|124|평균복당포유기간|Avg lactation days|= `avg_lactation_days`|①|보고서|Y(포유기간 규정차)|
|125|전산차분만모돈수|Farrowed sows(all parity)|분만 distinct 모돈|②|count|N|
|126|분만모돈두수|Farrowed sow count|동일|②|count|N|
|127|총분만간격|Total farrowing interval|Σ(연속 분만일차)|②|연속 사이클 차 합|N|
|128|평균분만간격|Avg farrowing interval|총/건수|②|평균|Y(목표차)|
|129|기간중교배복수|Matings in period|기간 mating count|①|total_matings|N|
|130|총모돈사육일수(후보포함)|Total sow days(incl gilt)|Σ 재고일수|②|재고×일수 적분|N|
|131|후보돈사육일수|Gilt days|GILT 상태 일수|③|GILT 상태 구간 추적 필요|N|
|132|임신일수|Gestation days(agg)|Σ 임신 구간|②|상태구간 합|N|
|133|포유일수|Lactation days(agg)|Σ 포유 구간|②|상태구간 합|N|
|134|모돈생산일수(임신+포유)|Productive days|임신+포유 일수|②|합|N|
|135|총비생산일수(NPD)|Total NPD|총사육일−생산일 = NPD|①|룰엔진 NPD|Y|
|136|후보돈포함총비생산일수|Total NPD incl gilt|위 + GILT NPD|②|GILT 포함 변형|Y|
|137|평균비생산일수|Avg NPD|NPD/모돈수|①|룰엔진/보고서|Y(목표차)|
|138|후보돈포함평균비생산일수|Avg NPD incl gilt|위/모돈수|②|변형|Y|
|139|모돈회전율(LSY)|Litters/sow/year|분만복수/모돈/년 = LSY|①|metric_code LSY(시드 존재)|Y(목표차)|
|140|후보돈포함모돈회전율|LSY incl gilt|GILT 포함 변형|②|변형|Y|
|141|PSY|Pigs weaned/sow/year|= metric PSY|①|룰엔진/스냅샷 PSY|Y(시장별 목표 큼)|
|142|후보돈포함PSY|PSY incl gilt|GILT 포함 변형|②|변형|Y|
|143|PSY(대모제외)|PSY excl nurse sows|대리모 제외 PSY|②|대리모 플래그 분해|Y|
|144|후보돈포함PSY(대모제외)|PSY incl gilt excl nurse|조합 변형|②|변형|Y|
|145|MSY|Pigs sold/sow/year|= metric MSY|①|시드/룰 MSY (출하 연계)|Y(시장별 목표 큼)|
|146|MSY(자돈출하포함)|MSY incl weaner sales|자돈출하 포함 MSY|③|자돈 판매·출하 연계 데이터 필요|Y|

---

## 분류 집계 (요약)

- **① 이미 계산: 22개** — 22,49,60,71,72,78,79,84,85,99,100,113,117,118,120,124,129,135,137,139,141,145
- **② 데이터 있음·미집계: 98개** — 대부분 count/비율/기간 적분 (이벤트 필드 존재, 집계만 추가).
- **③ 데이터 부족: 26개** — 생시체중 계열(86~89,102,109,114), 분만 4구분(74~77), 재포유(111,116), 부분이유(119), 생시도태(97,98), 후보돈 사육일수·전입일령·초교배일령(5,18,46,131), 복당임신사고일수(94), MSY 자돈출하(146).
- **국가차등 Y: 41개** (R2 대상) — 비율·효율 KPI(PSY/MSY/LSY/NPD/분만율/재귀율/이유두수/PWMR/도폐사율 등) + 정의·관습 차이(이유일령104, 포유기간124, 초교배일령46, 보정21일체중102).

## ③(데이터 부족) 해소에 필요한 입력 설계 (R3 백로그 후보)
1. **생시체중** — Farrowing에 litter/piglet birth weight 컬럼 + 입력 UI (생시체중 7지표 해소).
2. **분만 구분 4종** — farrowing_ease(난이도)와 별개로 `farrowing_type`(정상/조산/유도/사고) 필드.
3. **보정 21일령 체중 + 재포유** — 이유 체중 측정 + 재포유 이벤트.
4. **GILT 상태구간 추적** — 후보돈 사육일수/전입일령/초교배일령(sow.birth_date·entry_date 신뢰 확보).

## 우선순위(R3에서 점진 확장할 ②지표 상위 — 이미 원천 있음)
교배 분해(23~33), 사산/미라(80,81,90~93), WSI 분포(50~59, 58/59 비율), 수태율(95),
평균이유일령(104)·이유체중(105), 양자(108), 평균분만간격(128), LSY/PSY/NPD 변형(136,138,140,142).
</content>
