# PigOS 메뉴(사이드바) 재설계 — 확정안 (2026-06-18)

> 결정: ① PigPlan식 그룹 재편 ② '관리알림'+'알림' → '알림' 하나로 통합 ③ '분만사(Farrowing)' 메뉴 제거.
> 적용 위치: `src/components/Sidebar.tsx`(NAV_GROUPS/BOTTOM_ITEMS) + `src/messages/{en,ko,zh,es,vi}.json`(nav.*).
> ⚠️ cowork 밤샘 잡(messages·components 편집)과 충돌 방지 → **cowork 종료 후 적용**.

---

## 1. 확정 구조 (위→아래)

| 순서 | 그룹 | 항목(route) | 비고 |
|---|---|---|---|
| 1 | — | **대시보드** `/` | 생산현황 요약 |
| 2 | — | **기록 입력** `/record` | 단독 1차 액션(PigPlan '○○기록입력' 통합 진입: 교배·분만·이유·사고·자돈폐사 탭) |
| 3 | **돈군** | 모돈 `/sows` · 웅돈 `/boars` · 자돈 `/piglets` · 비육돈 `/finishers` | "관리" 군더더기 제거 |
| 4 | **할 일·알림** | 오늘 할 일 `/tasks` · **알림 `/alerts`(통합)** | 오늘할일을 기록그룹에서 이동 / 관리알림+시스템알림 통합 |
| 5 | **보고서** | KPI 현황 `/kpi` · 생산성적 `/reports/reproduction` · 비육성적 `/reports/grow-finish` · 모돈 보고서 `/reports` · PRRS 유전 `/reports/prrs` | '분석'→'보고서', 보고서류 평면나열을 명확한 이름으로 |
| 6 | — | Addon 스토어 `/addons` · 설정 `/settings` | 하단 유지 |

### 현행 대비 변경점
- **제거**: `분만사 /farrowing` 메뉴 항목(라우트는 남기되 메뉴에서 뺌).
- **통합**: `알림 /notifications` 메뉴 제거 → `알림 /alerts` 하나로. 통합 페이지는 **탭 2개**(관리대상=과기한 모돈/도태권고 · 시스템알림=읽음처리). badge=관리대상+미읽음 합산.
- **이동**: `오늘 할 일`을 '기록' 그룹 → 신설 '할 일·알림' 그룹으로.
- **재그룹/개명**: '분석' → '보고서', `KPI`를 보고서 그룹 첫 항목으로 흡수, 보고서 항목명 명확화.
- **개명**: '돈군 관리' → '돈군'.

---

## 2. i18n 라벨 (en / ko / zh / es / vi) — nav.* 키

| key | en | ko | zh | es | vi |
|---|---|---|---|---|---|
| nav.dashboard | Dashboard | 대시보드 | 总览 | Panel | Tổng quan |
| nav.record | Record Entry | 기록 입력 | 记录录入 | Registro | Nhập dữ liệu |
| **그룹** herd | Herd | 돈군 | 猪群 | Hato | Đàn heo |
| nav.sows | Sows | 모돈 | 母猪 | Cerdas | Heo nái |
| nav.boars | Boars | 웅돈 | 公猪 | Verracos | Heo nọc |
| nav.piglets | Piglets | 자돈 | 仔猪 | Lechones | Heo con |
| nav.finishers | Finishers | 비육돈 | 育肥猪 | Engorde | Heo thịt |
| **그룹** tasksAlerts | Tasks & Alerts | 할 일·알림 | 任务与预警 | Tareas y alertas | Việc & cảnh báo |
| nav.tasks | Today's Tasks | 오늘 할 일 | 今日任务 | Tareas de hoy | Việc hôm nay |
| nav.alerts | Alerts | 알림 | 预警 | Alertas | Cảnh báo |
| **그룹** reports | Reports | 보고서 | 报告 | Informes | Báo cáo |
| nav.kpi | KPI Summary | KPI 현황 | 指标概览 | Resumen KPI | Tổng quan KPI |
| nav.reproReport | Production (Repro) | 생산성적 | 繁殖成绩 | Producción | Năng suất sinh sản |
| nav.growFinish | Grow-Finish | 비육성적 | 育肥成绩 | Engorde | Năng suất vỗ béo |
| nav.sowReport | Sow Report | 모돈 보고서 | 母猪报告 | Informe de cerdas | Báo cáo nái |
| nav.prrs | PRRS Genetics | PRRS 유전 | PRRS基因 | PRRS genética | PRRS di truyền |
| **그룹** more / nav.addons / nav.settings | (현행 유지) | | | | |

> 그룹 헤더 라벨도 nav.* 또는 기존 그룹 키 패턴으로 5개어 동시 추가(누락 금지).

---

## 3. 적용 체크리스트 (cowork 종료 후)
- [ ] `Sidebar.tsx` NAV_GROUPS 재구성(위 표) + BOTTOM_ITEMS에서 notifications 제거, alerts를 '할 일·알림' 그룹으로.
- [ ] `/farrowing` 메뉴 항목 제거(라우트/페이지는 보존).
- [ ] `/alerts` 페이지 = 관리대상 탭 + 시스템알림 탭 통합(기존 `/notifications` 콘텐츠 흡수). badge 합산.
- [ ] 5개어 nav.* 키 추가/개명(en/ko/zh/es/vi), 미사용 키 정리.
- [ ] data-testid 유지(E2E `nav-*` 셀렉터) — 라우트 기반이라 그대로 동작, 단 nav-notifications 테스트 제거/대체.
- [ ] `npx tsc --noEmit` + `test:e2e:smoke`(메뉴 라우팅) green.
