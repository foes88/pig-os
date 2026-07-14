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

> 2026-07-13 버그헌터 4기(sows/record·reports·alerts/settings/admin·finishers/chat) 동시 수색 → 확인된 결함 일괄 수정.

| # | 화면 | 증상 | 원인 | 심각도 | 상태 |
|---|------|------|------|--------|------|
| BUG-001 | /alerts + Sidebar | 배지 "2"인데 첫 화면 빈 화면 | 배지=overdue+미읽음 합산, 착지 탭은 overdue만 | 中 | ✅ AlertsTabs 탭별 건수 배지 |
| BUG-002 | /record 분만 | 평균 생시체중·분만난이도 입력이 저장 안 됨 | create body에서 `avg_birth_weight_kg`/`farrowing_ease` 누락(타입도 누락) | 中 | ✅ 전송+타입 추가 |
| BUG-003 | /record 최근이벤트 | 수정/삭제 후 좌측 목록·헤더 배지 stale | RecentEventsSection이 sows.detail만 무효화(목록 prefix 불일치) | 中 | ✅ onChanged로 sows.all 무효화+선택동기화 |
| BUG-004 | 이벤트 삭제(API) | 재교배 후 옛 이유 삭제 시 상태 붕괴 | delete_weaning 무조건 LACTATING 롤백+옛 사이클 재개 | 中 | ✅ 재교배 전방 가드 409 |
| BUG-005 | 리포트 4종 | 월말일에 기간 시작월 1개월 밀림 | `monthsAgoISO` setMonth 오버플로 | 中 | ✅ setDate(1) 선행 |
| BUG-006 | /alerts/[type] | 분만지연 알림 "액션"이 교배 탭(막힘) | meta.action="mating"(PREGNANT는 교배 거부) | 中 | ✅ farrowing 탭+i18n |
| BUG-007 | /chat | 모든 언어 사용자에게 한국어 답변 | locale 하드코딩 "ko" | 高 | ✅ UI 로케일 전송 |
| BUG-008 | /chat (백엔드) | ru 사용자 chat 422 | ChatQuery 패턴에 ru 없음 | 中 | ✅ ru 허용+타입 확장 |
| BUG-009 | /boars | 필터 전환 시 빈 표+페이저 소실(스트랜딩) | page 클램프/리셋 없음 | 中 | ✅ safePage+setPage(1) |
| BUG-010 | /settings/profile | 저장 버튼 no-op(가짜 토스트) | handleSave가 API 미호출 | 中 | ✅ PATCH /me 실제 연동 |
| BUG-011 | /admin/rules | below형(PSY/분만율) 정상 임계 저장 거부 | `warning<critical` 무조건 강제 | 中 | ✅ 방향-인지 검증(below형 warning>critical / above형 warning<critical). ⚠️초기 "동일값만 거부"는 above형 회귀→pytest로 포착·정정 |
| BUG-012 | /admin/rules | 저장 실패 무피드백 | mutation onError 없음 | 低 | ✅ 에러 배너 |
| BUG-013 | finishers/boars/piglets | 기본 limit 초과분 조용히 유실 | 프론트가 limit 미전송 → 서버 기본(50/100) 캡 | 中 | ✅ 엔드포인트 최대(200/500/200) 요청 |
| BUG-014 | /admin/data-monitor | ru 사용자 영어 노출 | 인라인 T에 ru 누락 | 低 | ✅ ru 추가 |

| BUG-015 | ReportsTabs·QuickInput·AskAi·Sidebar·대시보드·원가리포트 | th/pt/ru 사용자 영어 노출 | 인라인 라벨이 5개어만 정의 | 中 | ✅ 8개어 보강 |
| BUG-016 | sync piglet_event | target_sow_id 미검증 저장(dangling FK) | 오프라인 sync가 REST의 인-팜 검증 누락 | 低 | ✅ 인-팜 검증+SyncRejected |

### 3차 보안감사 결과 (2026-07-15)
- **테넌트 격리(farm_id IDOR)·RBAC·auth 전 경로 CLEAN** — path-id 조회가 dependency/service/query 3계층에서 farm_id 강제.
- `PATCH /me`는 name/phone만 수정(role/org/system_role 자기변경 불가) 확인.
- 잔여 hardening: support.create_ticket farm_id 멤버십 미검증(라벨 전용, 유출 아님) — 후속.

> 백엔드 pytest **실행 완료(2026-07-15, Docker 재기동 성공): 873 passed · 1 skipped · 0 failed**.
> delete_weaning 가드·PATCH /me·chat ru·sync target·annual-kpi 전부 통과. BUG-011 초기수정 회귀는 pytest가 포착→정정.

### 후속(별도 태스크)
- 진짜 서버 페이지네이션(offset+total) — finishers/boars/piglets. 현재는 최대치 요청으로 유실만 차단(200/500 초과 농장은 여전히 잘림).
- 알림 상세 "감지규칙/임계"가 하드코딩(114/21/7/240) — 농장 커스텀 설정 반영 안 됨(표시-계산 불일치 가능). `/config/repro` 연동 필요.
- 프로필 전화번호는 백엔드 저장되나, 사진 변경 버튼은 미구현.

### BUG-001 수정 방향(후보)
- (a) 배지를 탭별로 분리: Alerts 아이콘 배지는 overdue+cull만, 알림(종) 배지는 미읽음만.
- (b) /alerts 착지 탭을 "건수 있는 탭"으로 자동 선택(overdue 0 && unread>0 → Notifications 탭 오픈).
- (c) 배지 유지하되 Overdue 빈 화면에 "미읽음 알림 N건 있음 → Notifications 탭" 안내 링크.
- 추천: **(a)** — 의미가 다른 두 카운트를 한 배지에 합치지 않기. Sidebar `alertCount + unreadCount` 합산을 분리.
- 구현 지점: `src/components/Sidebar.tsx` L120·L127·L211-213 (배지 계산), `src/app/(app)/alerts/page.tsx` (탭 기본값).
