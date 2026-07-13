# PigOS 유저 테스트 플랜 (UAT Checklist)

> 목적: 전 화면을 사람이 직접 클릭하며 도는 수동 QA 플랜. 발견 버그는 §말미 버그로그에 누적.
> 작성 2026-07-13. 대상: 웹(pigos.io / admin.pigos.io). 모바일은 별도 handoff 문서.
> 진행 방식: 화면별 시나리오를 순서대로 실행 → `상태`에 ✅/❌/⏭️ 표기, ❌는 버그로그에 번호 부여.

---

## 0. 준비

| 항목 | 값 |
|------|-----|
| 테스트 계정(농장) | ezfarm / t@t.com (tfarm) — 스샷 확인됨 |
| 관리자 계정 | (admin 콘솔용 별도 계정) |
| 언어 | 8개 로케일 전환 각각 확인 (en/ko/zh/es/vi/th/pt/ru) |
| 데이터 상태 | 신규/소량 농장 → "데이터 없음" 빈 상태 UX가 1차 관심 |

**공통 점검(모든 화면)**: ① 빈 상태 문구가 자연스러운가 ② 로딩 스켈레톤 ③ 에러 시 메시지 ④ 배지/카운트가 실제 내용과 일치 ⑤ 언어 전환 시 깨짐 없는가 ⑥ 모바일 폭(≤768px) 레이아웃.

---

## 1. 인증 / 온보딩
- [ ] 로그인 성공/실패(잘못된 비번) 메시지
- [ ] 온보딩: 국가 선택 → 통화/타임존/단위 자동 채움, 국가별 입력필드 변화
- [ ] 이메일 인증 / 비번 재설정 플로우

## 2. 대시보드 (/)
- [ ] KPI 카드 값 표시 + 빈 농장 시 0/— 처리
- [ ] 관리대상 모돈 카드 → 클릭 시 /alerts 이동, 배지 숫자 일치

## 3. 돈군 관리
- [ ] /sows 목록·검색·필터, 등록/수정/도폐사·판매 모달
- [ ] /sows/[id] 상세 — 번식이력 타임라인, 산차별 성적, 이벤트 수정/삭제
- [ ] /boars 목록·CRUD·페이지네이션
- [ ] /piglets 자돈 현황
- [ ] /finishers 비육 그룹 목록/상세/주간입력/수정, 페이지네이션
- [ ] /feed 사료 기록

## 4. 기록 입력 (/record)
- [ ] 탭 전환(교배/분만/이유), 모돈 검색, 입력 검증(422) 메시지
- [ ] 최근 이벤트 이력 + 수정/삭제 → 모돈 상태 롤백
- [ ] 모바일 스택 레이아웃

## 5. 알림 / 알람 ⚠️ (BUG-001 관련)
- [ ] /alerts "Overdue & Cull" 탭 — 6유형 과기한 + 도태권고
- [ ] /alerts "Notifications" 탭 — 알림 목록, 읽음 처리, 유형 필터
- [ ] **사이드바 배지 숫자 == 착지 탭에서 실제 보이는 건수** (BUG-001: 현재 불일치)
- [ ] /tasks 오늘 할 일

## 6. 리포트 (13개 탭)
- [ ] /reports (생산성적) · /reproduction · /trend(연도추세) · /monthly(월별종합)
- [ ] /farrowing · /grow-finish · /cost · /comprehensive-daily · /daily
- [ ] /mortality · /prrs · /ledger · /sow-status · /data-quality
- [ ] **각 리포트 CSV 다운로드 + PDF(인쇄) 정상** (신규 확대 기능)
- [ ] 기간 프리셋 전환, 빈 데이터 시 문구
- [ ] /trend: 국가 벤치마크(KR/US/BR) 병기표, PSY/NPD 라인차트 기준선
- [ ] /monthly: 최근월 헤드라인 전월대비 화살표 방향(높을수록/낮을수록 좋음)

## 7. 설정
- [ ] /settings/farm — 임신/포유/WSI/초교배 목표 수정 → alert 기준 즉시 반영, 범위검증
- [ ] /settings/benchmarks · /thresholds · /profile · /users · /billing · /delete-account

## 8. Q&A / 기타
- [ ] /chat 질의 → Rule 기반 응답
- [ ] /addons 스토어, /announcements, /legal, /support

## 9. Admin 콘솔 (admin.pigos.io) — 한글 우선
- [ ] /admin/data-monitor 목록 → 이슈 카운트 컬럼, 행 클릭 → [farmId] 드릴다운
- [ ] [farmId]: KPI 카드·모돈상태·이벤트분해·데이터품질·최근활동
- [ ] /admin/orgs · /users · /rules · /master-data · /audit · /announcements · /support
- [ ] 언어 선택기(8개 + ko) 동작

---

## 버그 로그

| # | 화면 | 증상 | 원인(추정) | 심각도 | 상태 |
|---|------|------|-----------|--------|------|
| BUG-001 | /alerts + Sidebar | 배지 "2"인데 Alerts 페이지 첫 화면(Overdue & Cull) 빈 화면 | 배지 = `overdue.total + 미읽음알림` 합산인데, 착지 탭은 overdue(0)만 표시. 2는 Notifications 탭의 미읽음. **세는 값 ≠ 보이는 탭** | 中(혼란) | ✅ 수정(fix c…) — AlertsTabs 탭별 건수 배지 |

### BUG-001 수정 방향(후보)
- (a) 배지를 탭별로 분리: Alerts 아이콘 배지는 overdue+cull만, 알림(종) 배지는 미읽음만.
- (b) /alerts 착지 탭을 "건수 있는 탭"으로 자동 선택(overdue 0 && unread>0 → Notifications 탭 오픈).
- (c) 배지 유지하되 Overdue 빈 화면에 "미읽음 알림 N건 있음 → Notifications 탭" 안내 링크.
- 추천: **(a)** — 의미가 다른 두 카운트를 한 배지에 합치지 않기. Sidebar `alertCount + unreadCount` 합산을 분리.
- 구현 지점: `src/components/Sidebar.tsx` L120·L127·L211-213 (배지 계산), `src/app/(app)/alerts/page.tsx` (탭 기본값).
