# PigPlanCORE — Homepage Section Content

> pigplan 페이지 내 PigPlan / InsightPigPlan / PigSignal 과 동일한 Section 컴포넌트 사이즈로 배치
> 컨셉 전환: SaaS → AI 중심 플랫폼 (양돈 수익 최적화 AI 운영 시스템)

---

## 컨셉 방향

| 구분 | 기존 | 전환 방향 |
|------|------|----------|
| 제품 정의 | 양돈 관리 SaaS | **양돈 수익 최적화 AI 운영 시스템** |
| 기술 구조 | CRUD 기반 | **Event-driven + Time-series + AI Agent** |
| AI 역할 | 리포트/챗봇/추천 (보조) | **Agent 기반 의사결정 + 실행 (핵심)** |
| 과금 모델 | Per-seat 구독 | **Platform 무료 → Usage → Outcome 기반** |
| 투자 스토리 | Agri SaaS | **Vertical AI for Pig Farm Operations** |

**한 줄:** 데이터 → AI Agent → Action(실행). SaaS는 기록하는 시스템, AI는 돈을 만들어주는 시스템.

---

## i18n Keys: `pigplanCore`

### KO

```json
{
  "pigplanCore": {
    "label": "PigPlanCORE",
    "title": "기록이 아니라, 수익을 만드는 시스템",
    "subtitle": "AI Agent가 농장 데이터를 분석하고, 의사결정을 내리고, 실행까지 연결합니다.",
    "desc": "PigPlanCORE는 단순 관리 SaaS가 아닙니다. 데이터가 들어오면 AI가 분석하고, 지금 무엇을 해야 하는지 알려주고, 실행까지 이어지는 양돈 수익 최적화 AI 운영 시스템입니다.",
    "features": {
      "f1_title": "AI Agent 의사결정",
      "f1_desc": "폐사율 감소, 사료 효율 개선, 출하 수익 증가 — 수치로 증명하는 AI",
      "f2_title": "데이터 → 행동",
      "f2_desc": "알림이 아니라 Action. '지금 무엇을 해야 하는가'까지 제시",
      "f3_title": "글로벌 벤치마크",
      "f3_desc": "5개 시장 실시간 비교. 내 농장이 세계 상위 몇 %인지 즉시 확인",
      "f4_title": "데이터 마켓플레이스",
      "f4_desc": "농장 데이터가 사료회사·종돈사·제약사와 API로 연결. 가치가 교환되는 장터"
    },
    "stats": {
      "markets": "5개 시장",
      "languages": "5개 언어",
      "agent": "AI Agent",
      "outcome": "성과 기반"
    },
    "marketplace": {
      "title": "데이터가 돈이 되는 구조",
      "desc": "농장의 데이터가 AI Agent를 통해 분석되고, API 마켓플레이스에서 사료회사·종돈사·제약사와 만납니다. 각자에게 가치 있는 인사이트로 돌아옵니다.",
      "flow1": "농장 데이터",
      "flow2": "AI Agent 분석",
      "flow3": "API 마켓플레이스",
      "flow4": "수익 환류"
    },
    "cta": "자세히 보기",
    "ctaPrototype": "프로토타입 보기"
  }
}
```

### EN

```json
{
  "pigplanCore": {
    "label": "PigPlanCORE",
    "title": "Not Records. Revenue.",
    "subtitle": "AI Agents analyze farm data, make decisions, and drive actions — automatically.",
    "desc": "PigPlanCORE is not just management SaaS. Data flows in, AI analyzes it, tells you what to do right now, and connects to execution. An AI-powered revenue optimization system for pig farms.",
    "features": {
      "f1_title": "AI Agent Decisions",
      "f1_desc": "Reduce mortality, improve feed efficiency, increase shipment revenue — proven by numbers",
      "f2_title": "Data → Action",
      "f2_desc": "Not alerts. Actions. 'What should I do right now?' answered instantly",
      "f3_title": "Global Benchmarking",
      "f3_desc": "Real-time comparison across 5 markets. See your farm's global ranking instantly",
      "f4_title": "Data Marketplace",
      "f4_desc": "Farm data connects with feed, genetics, and pharma companies via API. Value exchanged"
    },
    "stats": {
      "markets": "5 Markets",
      "languages": "5 Languages",
      "agent": "AI Agent",
      "outcome": "Outcome-based"
    },
    "marketplace": {
      "title": "Where Data Becomes Revenue",
      "desc": "Farm data is analyzed by AI Agents and meets feed companies, genetics firms, and pharma on the API marketplace. Actionable insights flow back to everyone.",
      "flow1": "Farm Data",
      "flow2": "AI Agent Analysis",
      "flow3": "API Marketplace",
      "flow4": "Revenue Returns"
    },
    "cta": "Learn More",
    "ctaPrototype": "View Prototype"
  }
}
```

---

## Image Prompts

### 1. 메인 히어로 — AI Agent가 농장을 운영하는 느낌
> **Prompt:** A futuristic isometric illustration of an AI-powered pig farm operations system. In the center, a glowing AI brain/agent icon connected to a holographic dashboard showing PSY, FCR, mortality charts. On the left, stylized farm buildings with data streams flowing upward into the AI. On the right, action arrows pointing to outcomes: a dollar sign (revenue up), a downward arrow (mortality down), a grain icon (feed optimized). Clean, minimal SaaS style. Color palette: dark navy (#0F172A), emerald green (#0D7C66), gold accents (#C9A84C). Dark background with subtle grid. No text.

### 2. 데이터 → AI Agent → Action 플로우
> **Prompt:** A horizontal flow illustration on dark background. Three stages connected by glowing lines. Stage 1 (left): Farm icons with data points floating up — temperature, pig silhouettes, feed bins. Stage 2 (center): A large glowing AI Agent hexagon processing data, with neural network patterns inside. Stage 3 (right): Action outputs — a calendar (breeding schedule), alert icon (disease warning), truck (optimal shipment timing), coin stack (revenue). Data particles flow left to right, transforming from raw (blue dots) to processed (gold dots). Futuristic, clean. Navy/green/gold palette. No text.

### 3. 데이터 마켓플레이스 — API끼리 Agent끼리 장터
> **Prompt:** An isometric dark-themed illustration of a data marketplace ecosystem. Center: a glowing circular platform/hub with the concept of a digital marketplace. Left side: multiple farm nodes sending green data streams into the hub, each with a small AI agent icon attached. Right side: corporate nodes (feed company with grain icon, genetics with DNA helix, pharma with molecule, research with chart) receiving gold data streams. AI agent robots travel along the connection lines, carrying data packets. The hub pulses with energy where data transforms into insights. Futuristic cyberpunk-lite aesthetic. Navy (#0F172A) background, green (#0D7C66) for farm data, gold (#C9A84C) for business insights. No text.

### 4. SaaS vs AI 비교 — 전환 컨셉
> **Prompt:** A split-screen comparison illustration. Left side (dimmer, grayscale-ish): Traditional SaaS — a person typing records into a computer, static spreadsheets, manual clipboard. Label area for "Records". Right side (vibrant, glowing): AI-powered system — an AI agent brain icon connected to automated dashboards, real-time alerts, money/revenue icons flowing. Label area for "Revenue". A dramatic arrow or transition effect from left to right. The right side radiates energy and movement while the left is static. Clean illustration style. Left: muted blue-gray. Right: vibrant navy + green + gold. No text.

### 5. 글로벌 5개 시장 연결 — AI가 전 세계를 연결
> **Prompt:** A dark globe illustration with 5 glowing hotspots for USA, China, Southeast Asia (Vietnam/Thailand), Latin America, and South Korea. Each hotspot has a small farm icon and an AI agent icon. Thin glowing green lines connect all hotspots through a central orbiting AI agent ring around the globe. Data particles travel along the lines between markets. The globe is semi-transparent with subtle country borders. Futuristic, premium feel. Navy background, green connection lines, gold accent on AI agents. No text.

### 6. Outcome 기반 — 성과로 증명
> **Prompt:** A clean dashboard-style illustration showing three outcome metrics as large glowing cards on a dark background. Card 1: Pig mortality icon with a large downward arrow and percentage (abstract). Card 2: Feed conversion icon with an efficiency gauge showing improvement. Card 3: Revenue/shipment icon with upward trending graph and coin symbols. Below the cards, a subtle timeline showing "Data In → AI Analysis → Action Taken → Outcome Achieved" as a horizontal flow. Premium SaaS analytics aesthetic. Dark navy background, green for positive metrics, gold for revenue. No text except abstract numbers/symbols.

---

## 컴포넌트 배치

```
pigplan/page.tsx:

<PageHero namespace="pages.pigplan" />
<PigPlanSection showHeader={false} />         ← 기존 피그플랜
<PigPlanCoreSection />                        ← 새로 추가 (이 문서)
<PartnerMarquee />
<InsightPigPlanSection />
<PigSignalSection />
```

PigPlanCoreSection은 기존 PigPlanSection / InsightPigPlanSection과 동일한 `<Section>` 컴포넌트 사용. 동일한 `grid lg:grid-cols-2 gap-16 items-center` 레이아웃.

**구성:**
- Left: label + title + subtitle + desc + 4개 feature 카드 (2x2 grid)
- Right: 메인 이미지 (히어로 또는 데이터→AI→Action 플로우)
- Below (full-width): 데이터 마켓플레이스 섹션 (flow1→flow2→flow3→flow4 수평 플로우)
- Stats: 4개 수치 카드 (5개 시장 / 5개 언어 / AI Agent / 성과 기반)
- CTA: 자세히 보기 + 프로토타입 보기

---

## 네이밍 후보 (참고)

| 이름 | 포지셔닝 | 강점 |
|------|----------|------|
| **PigOS AI** | 농장 운영 체제 | 플랫폼 전략과 일치, 투자자 스토리에 강함 |
| **PigOps AI** | 운영 최적화 실행 | B2B 현장 친화적, 실행/자동화 뉘앙스 |
| **PigCore AI** | 핵심 플랫폼 + 확장성 | 장기 브랜드 내구성, 축산 확장 시에도 유효 |

*최종 네이밍 미확정. 대외 브랜딩과 내부 제품명 분리 검토 중.*
