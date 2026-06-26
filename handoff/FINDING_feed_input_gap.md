# 발견 — 수기 급이량(Feed) 입력 경로 부재 (랜딩 'Feed' 전제)

> 2026-06-25 확인. 사용자 1순위 질문("Core가 수기 급이량 저장하나") 결과.

## 결론
**모델·계산식은 있으나 입력 경로가 없어 feed_records는 사실상 빈 테이블 → FCR 실데이터 0 → 현재 'Feed'를 랜딩에 올릴 수 없음.**

| 층 | 상태 | 근거 |
|---|---|---|
| 저장 모델 | ✅ 있음 | `feed_records.quantity_kg`(급이량, NOT NULL) + record_date·feed_type·unit_cost·currency·sow/group/building·soft-delete (`api/app/db/models/health.py:41`) |
| 소비(읽기) | ✅ 있음 | FCR = `SUM(feed_records.quantity_kg)/증체량` (`kpi_service.py:255,340`), grow-finish 리포트(`report_service.py:427`) |
| **수기 입력(쓰기)** | ❌ **없음** | `FeedRecord(` 생성 코드 0 / feed 라우터 0 / OpenAPI feed 0 / 프론트 입력화면 0 / sync·event 미처리 |

## Feed 모듈 성립 조건 (입력구 신설 필요)
1. **쓰기 API** — `POST /api/v1/farms/{farm_id}/feed-records` (또는 event_service에 FEED 이벤트 타입; `event_definitions`에 FEED 카테고리는 이미 존재).
   - 필드: record_date, feed_type, quantity_kg, 대상(sow_id|group_id|building_id), unit_cost?·currency?
   - 검증: quantity_kg>0, 대상 1개 이상, period_locks 잠금 검사(423).
2. **입력 UI** — `record` 화면에 "사료 급여" 탭/폼 (7개어 i18n).
3. (선택) **sync 경로** — 오프라인 현장 입력(sync_queue).
4. 테스트 — 쓰기→FCR 반영 E2E.

## 영향
- FCR·grow-finish 리포트는 입력 들어와야 실값. 그 전엔 None/0.
- 랜딩 'Feed'/'FCR' 문구는 입력구 완성 후 노출.

## 결정 대기
- Feed 입력 경로를 **언제 만들지**(지금/출시 전/P2). 만들면 위 1~4 범위.
