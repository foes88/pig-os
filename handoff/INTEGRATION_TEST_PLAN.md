# 통합테스트 플랜 (PigOS) — 2026-06-29

> 목적: 단위 위주 커버리지(백엔드 726 / 프론트 62) 위에, **실제 사용자 플로우 end-to-end**와
> **이벤트→집계 수치 정합성**을 못박아 "배포해도 안 망하는" 확신을 만든다.
> 원칙: 실서비스(record_*)·실라우터로 기록 → 산출물(보고서/KPI/상태) 수치를 단언.

## 플로우별 상태

| # | 플로우 | 상태 | 비고 |
|---|--------|------|------|
| F1 | 번식 사이클(교배→임신→분만→이유) 상태전이 | ✅ | test_full_breeding_cycle |
| F2 | 검증 게이트(두수/날짜/상태 422) | ✅ | test_validation_errors, p0_validations, uat_count_caps |
| F3 | 월마감 잠금(create/update/delete 423) | ✅ | period_locked_t4 + C2(이번 세션) |
| F4 | 오프라인 sync(배치→사이클/KPI 정합) | ✅ | sync_cycle_integrity_c4, sync_* |
| F5 | RBAC(역할×엔드포인트 200/403) | ✅ | farm_write_rbac, thresholds_perm |
| F6 | 멀티팜 계층 접근(총판 서브트리/타농장 차단) | ✅ | org_hierarchy_access, farm_access, uat(F1) |
| F7 | 관리자 콘솔 조직 CRUD | ✅ | admin_orgs(B5) |
| **F8** | **이벤트 기록(실서비스)→번식보고서 수치 일치** | **🔴 갭** | test_reports는 직접 insert만 — record_* 풀체인 미검증 → **이번에 추가** |
| F9 | 보고서 빈 기간 행 채움(트렌드와 일치) | 🟡 M4 | 미수정(행 누락) |
| F10 | 일별보고서 농장 타임존 | 🟡 M5 | 서버 KST 고정(비-KST off-by-one) |
| F11 | 알림 심각도 에스컬레이션 재알림 | 🟡 M1 | WARNING→CRITICAL 억제 |

## 우선순위 실행
1. **F8 이벤트→보고서 reconciliation**(최우선, 사용자 핵심 우려) — ✅ 이번에 추가
2. F9/F10/F11 — 후속(보고서 정합성·알림)
3. 대규모 30농장 시드 reconciliation(부록 B) — 주말 자율 런

## 잔여 결함(UAT, 미수정)
- M1 알림 에스컬레이션 억제 / M3 양자 정정경로 없음 / M4 빈기간 / M5 타임존
- F2 조직롤이 서브트리 농장에 write 불가(제품 결정 필요) / F3 reassign_farm 검증약함 / F4 org_level 미재계산
