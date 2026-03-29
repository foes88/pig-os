# PigOS AI — Design History & Decision Log

> 시안 변경 이력 · 의사결정 기록 · 나중에 디자인 변경 시 참고용

---

## v1 — 초기 시안 3종 (2026.03.19)

디자인 스펙 문서(`biz-report-os/projects/pig-os-ai/ui-concepts/`) 기반으로 제작.

| 파일 | 컨셉 | 색상 | 타겟 |
|------|------|------|------|
| `archive/v1-initial-concepts/v2-concept-A-harvest.html` | Harvest — 따뜻한 크림톤 | #C8832A 황금 | 국내 농장주, SEA |
| `archive/v1-initial-concepts/v2-concept-B-signal.html` | Signal — 다크 터미널 | #00D4FF 시안 | 미국 Integrator, EU |
| `archive/v1-initial-concepts/v2-concept-E-pulse.html` | Pulse — 라임 모던 | #B8FF00 라임 | 글로벌, 투자자 PT |

**결과: 전부 탈락**
- 사유: 전체적으로 마음에 안 듦. 방향 재설정 필요.

---

## v2 — 5종 시안 (2026.03.19)

공통 디자인 가이드 기반으로 재제작:
- Color: Deep Green (#0D7C66) + Blue Gray + Amber (#E8820E)
- Font: Inter + JetBrains Mono
- Style: Clean enterprise SaaS, modern technology platform
- No rustic/old-fashioned farm style

| 파일 | 컨셉 | 포커스 | 특장점 |
|------|------|--------|--------|
| `01-enterprise-dashboard.html` | Enterprise Dashboard | 경영진 종합 현황 | KPI + Chart.js 차트 + 랭킹 테이블 |
| `02-farm-operations.html` | Farm Operations | 현장 작업 중심 | 오늘 할 일, 큰 버튼, 직관적 |
| `03-smart-ai.html` | Smart AI Platform | AI 인사이트 | 예측, 이상탐지, 추천 — 차별화 |
| `04-herd-management.html` | Herd Management | 돈군 그룹 관리 | 필터, Card+Table 하이브리드 |
| `05-breeding-workflow.html` | Breeding Workflow | 번식 파이프라인 | 교배→분만→이유 프로세스 시각화 |

**비교 도구:**
- `compare.html` — 5분할/3분할/2분할 iframe 비교 뷰
- `index.html` — 카드형 시안 선택 페이지

---

## v3 — Combined MVP (2026.03.19)

**선택: 02 + 03 + 05 합본**

| 요소 | 출처 | 역할 |
|------|------|------|
| AI 배너 + AI 추천 카드 + AI 예측 패널 | 03 Smart AI | 차별화 포인트 |
| 오늘 할 일 + Task 리스트 + Quick Actions | 02 Farm Operations | 직관적 사용성 |
| 번식 파이프라인 + 분만 타임라인 | 05 Breeding Workflow | 양돈 특화 프로세스 |

**결정 사유:**
- 02번이 사용자 친화적/직관적으로 가장 우수
- 03번 AI 기능이 경쟁사 대비 차별화 핵심
- 05번 파이프라인이 양돈 SW의 존재 이유(번식 사이클) 시각화에 최적

**파일:** `combined-v1.html`

---

## 참고: 공통 디자인 토큰

```css
--primary: #0D7C66 (Deep Green/Teal)
--accent:  #E8820E (Amber/Orange)
--danger:  #DC2626
--success: #16A34A
--purple:  #7C3AED (AI 기능 전용)
--blue:    #2563EB
--bg:      #F4F6F8
--surface: #FFFFFF
--border:  #E2E8F0
Font: Inter (UI) + JetBrains Mono (Data)
```

---

*최종 업데이트: 2026.03.19*
