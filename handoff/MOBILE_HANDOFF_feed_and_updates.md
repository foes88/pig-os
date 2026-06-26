# 모바일 핸드오프 — 신규 기능 반영분 (pigos-ios / pigos-android)

> 2026-06-25. PigOS Core(이 레포)에 추가된 것 중 **모바일에 반영 가능한 것** 정리.
> 모바일 세션: `git pull` 후 이 문서 + 아래 계약 참조. Core가 검증 권위(서버 검증 그대로 따름).

---

## ★ 1. Feed(수기 급이량) 입력 — **모바일 추가 1순위 (오프라인-퍼스트 적합)**
배경: Core에 feed 저장모델·FCR 계산은 있었으나 **입력 경로가 없어** FCR이 빈 입력이었음. 이번에 입력 API 신설 → 모바일 현장 입력에 딱 맞음(농가가 "사료 몇 kg" 적는 화면).

**엔드포인트 (신규)**
```
POST   /api/v1/farms/{farm_id}/feed-records      (WORKER+ 권한)
GET    /api/v1/farms/{farm_id}/feed-records       ?limit=&offset=
DELETE /api/v1/farms/{farm_id}/feed-records/{id}  (관리자)
```
**요청 바디(POST)**
```json
{ "record_date": "2026-06-25", "quantity_kg": 1200.5,
  "feed_type": "비육|임신돈|포유돈 등(선택)",
  "group_id": "uuid(선택)", "building_id": "uuid(선택)", "notes": "(선택)" }
```
**검증(서버, 모바일도 동일 클라검증 권장)**
- `quantity_kg > 0` (필수, 0/음수 거부)
- 대상(sow_id/group_id/building_id)은 **최대 1개** (둘 이상 지정 시 422)
- 월마감 잠금 기간이면 **423** (아래 §2)
- soft-delete (deleted_at)

**모바일 작업**
- 입력 화면: 날짜·사료종류·급여량(kg)·(선택)대상 그룹. 오프라인 큐(sync_queue) 대상에 feed_records 추가.
- 최근 기록 목록 + 삭제.
- i18n: 웹 `src/messages/*.json`의 `feed.*` 15키(en/ko/zh/es/vi/th/pt) 그대로 재사용 가능(아래 §4).
- 동기화: Last-Write-Wins, farm_id 스코프(기존 sync 규약 동일).

---

## ★ 2. PeriodLockedError → HTTP **423** (이벤트 입력/수정/삭제 공통)
월마감(period_locks)된 기간의 데이터를 수정 시도하면 서버가 **423 Locked** 반환(이전 비일관 409 제거).
**모바일 작업**: 이벤트(교배/분만/이유/사료 등) 생성·수정·삭제 호출에서 **423 처리** 추가 — "마감된 기간입니다. 잠금 해제 후 수정하세요." 메시지. 응답 body: `{"code":"PERIOD_LOCKED","detail":"Period YYYY-MM is locked..."}`.

---

## 3. D-7 KR 경제지표 게이트 (참고 — 모바일 영향 적음)
`loss.sow_culling`(모돈 조기도태 손실, 원화 잔존가)이 **country='KR' 농장에서만** 발화하도록 게이트됨. 非KR 농장은 이 손실 인사이트가 안 뜸(원화 누수 방지). 모바일은 인사이트를 서버에서 받아 표시만 하므로 **별도 작업 없음**(KR 외엔 해당 카드가 안 올 뿐).

---

## 4. i18n — feed 7개어 키 (재사용)
웹 `src/messages/{en,ko,zh,es,vi,th,pt}.json`의 `feed` 섹션 15키:
`title·subtitle·add·recordDate·feedType·feedTypePlaceholder·quantityKg·save·saving·recent·empty·delete·qtyError·saveError·noFarm`
→ 모바일 문자열 리소스에 그대로 이식(번역 완료본).

---

## 5. 지금은 반영 보류 (서버 미활성/미완)
- **KPI Governance(3-table benchmark)·verified 국가평균 비교맥락**: 서버에 들어왔으나 **flag OFF(USE_GOVERNANCE_BENCHMARKS=false)**라 아직 발화 비활성. flag ON·임계정책 확정 후 모바일에 "국가 평균 대비" 비교 UI 추가 예정. **지금은 대기.**
- **챗 cause/action 코드 다국어**: 비-en/ko는 영어 폴백 상태(현지화 미완). 모바일 챗도 동일 한계 — 추후.

---

## 6. 요약 (모바일이 지금 할 일)
1. **Feed 입력 화면 + 오프라인 동기화** (POST/GET/DELETE feed-records) ← 최우선
2. **423 PeriodLocked 처리** (이벤트 입력/수정/삭제 공통)
3. feed 7개어 문자열 이식
4. (대기) governance 비교맥락 / 챗 현지화 — 서버 활성 후
