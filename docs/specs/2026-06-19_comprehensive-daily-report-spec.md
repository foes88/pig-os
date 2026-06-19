# 종합일보 (Comprehensive Daily Report) — PigPlan → PigOS 매핑

> 출처: PigPlan 종합일보 .mrd 쿼리(8섹션, Oracle FN_*/TB_* 기반). 사용자 제공 `종합일보.md`.
> 변환 원칙: PigPlan DB 함수/코드 → **PigOS 스키마(events/sow/health/ops)로 의도만 이식**. 일계(당일)+월계(당월 누적) 2열.
> 엔드포인트: `GET /api/v1/farms/{farm_id}/reports/comprehensive-daily?date=YYYY-MM-DD`

## 섹션별 매핑

### ① 돈군 현황 (모돈/웅돈/자돈/비육 재고) — 당일 스냅샷
PigPlan: `FN_MD_STOCK_2021`(후보/대기/재발정/임신/포유) + `FN_UD_DUSU_STATUS01`(웅돈) + `FN_MODON_BET_POUEU_STOCK`(포유자돈) + `FN_JD_DUSU_INFO_01`(비육 일령구간).
→ **PigOS**:
- 모돈: `sows.status` 집계 GILT/OPEN(대기)/ACCIDENT(재발정)/PREGNANT(임신)/LACTATING(포유)
- 웅돈: `boars.status='ACTIVE'` count
- 포유자돈: 활성 분만(미이유)들의 잔여 포유두수 Σ(nursing_head − Σweaned − deaths…) = `Σ(farrowing 잔여)`
- 비육: `finisher_groups` 활성(end_date null) head 합. (일령구간 70/105/140 분해는 그룹시작일 기반 근사 — ②와 공유)

### ② 비육 현황 (그룹별) — 당일
PigPlan: 그룹별 일령/장소/목표체중/입식/금일·누적폐사/육성율/전출/출하/재고/예정출하일.
→ **PigOS**: `finisher_groups` 행별 {group_code, start_date, 현재일령(=today−start_date), head_in, head_out, 잔여=in−out}. ⚠️ 장소/목표체중/일당증체/일별폐사는 PigOS 미보유 → 해당 컬럼 생략(그룹단위 핵심만).

### ③ 교배 현황 — 일계/월계
PigPlan: `TB_MODON_WK` WK_GUBUN='G', 산차/교배횟수로 후보(SANCHA=0,CNT=1)/경산(SANCHA>0,CNT=1)/후보재발(SANCHA=0,CNT≥2)/2·3·4차소피.
→ **PigOS**: `matings`(deleted_at null) JOIN sow.parity, mating_number.
- 총교배, 후보(parity=0 & mating_number=1), 경산(parity>0 & mating_number=1), 재교배(mating_number≥2). 당일 + 당월.

### ④ 임신사고 현황 — 일계/월계
PigPlan: `VW_MODON_2020_WK` WK_GUBUN='F', SAGO_GUBUN_CD별 + 교배후 경과일 버킷(≤17/18~25/26~37/38~46/47~80/81+).
→ **PigOS**: `reproductive_events` event_type∈(RETURN_TO_ESTRUS,ABORTION,EMPTY,INFERTILE) + 직전 mating_date와의 경과일 버킷. 당일+당월.

### ⑤ 생산현황 (분만·이유) — 일계/월계
PigPlan: 분만(총산=실산+사산+미라, 생시체중) + 이유(이유두수, 이유체중, 이유일령) + 자돈 도태/압사/설사/기타.
→ **PigOS**:
- 분만: `farrowings` count, Σtotal_born/born_alive/stillborn/mummified, avg `avg_birth_weight_kg`(P0 신규 컬럼)
- 이유: `weanings` 복수, Σweaned_count, avg `avg_weaning_weight_kg`, avg `weaning_age_days`
- 자돈폐사: `piglet_events` event_type=DEATH, reason별(CRUSHING=압사, SCOURS/STARVATION 등). 당일+당월.

### ⑥ 전입출·폐사 현황 — 일계/월계
PigPlan: 모돈 후보입식/경산입식/폐사/후보도태/기타판매 + 웅돈 입/출 + 비육폐사(일령구간) + 출하(위탁/자돈/비육/종돈)+출하일령 + 포유폐사.
→ **PigOS**:
- 모돈 입: `sows.entry_date` (entry_type=GILT→후보, 그외→경산 근사)
- 모돈 출: `removals.removal_type` DEAD=폐사 / CULLED·SOLD·TRANSFER=도태·판매·전출
- 웅돈 입/출: `boars.entry_date` / status 변경(출 데이터 제한적)
- 비육 폐사/출하: `finisher_groups` head_out(출하). ⚠️ 비육 일별폐사·일령구간폐사는 미보유 → 그룹 출하 중심
- 포유폐사: `piglet_events` DEATH (⑤와 동일원천, 여기선 전입출 맥락 재노출)

### ⑦⑧ 사료/도축 거래 — **제외**
PigPlan `TM_ETC_TRADE`(사료 F_KG/금액, 도축 carcass 등급/단가). PigOS **사료·거래 모듈 없음**(MVP_SCOPE v1.1) → 종합일보에서 제외. 모듈 생기면 추가.

## 응답 구조(안)
```
{ date, herd:{...①}, finishers:[...②], mating:{day:{...}, month:{...}},
  accidents:{day:{...}, month:{...}}, production:{day:{...}, month:{...}},
  inout:{day:{...}, month:{...}} }
```
기존 `/reports/daily`(간이)는 유지, 본 `comprehensive-daily`는 PigPlan 종합일보 대응 풀버전.
