# PigOS AI — Homepage Section Content

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
    "label": "PigOS AI",
    "title": "기록이 아니라, 수익을 만드는 시스템",
    "subtitle": "AI Agent가 농장 데이터를 분석하고, 의사결정을 내리고, 실행까지 연결합니다.",
    "desc": "PigOS AI는 단순 관리 SaaS가 아닙니다. 데이터가 들어오면 AI가 분석하고, 지금 무엇을 해야 하는지 알려주고, 실행까지 이어지는 양돈 수익 최적화 AI 운영 시스템입니다.",
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
      "languages": "7개 언어",
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
    "label": "PigOS AI",
    "title": "Not Records. Revenue.",
    "subtitle": "AI Agents analyze farm data, make decisions, and drive actions — automatically.",
    "desc": "PigOS AI is not just management SaaS. Data flows in, AI analyzes it, tells you what to do right now, and connects to execution. An AI-powered revenue optimization system for pig farms.",
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
      "languages": "7 Languages",
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

> 모든 이미지는 `grid lg:grid-cols-2`의 오른쪽 영역에 배치.
> 비율: **16:9** (aspect-video) 또는 **4:3**.
> 배경: 라운드 카드 안에 들어가므로 **rounded-2xl** 모서리에 맞게.
> 기존 PigPlanSection(Stats 카드), InsightPigPlanSection(유튜브 영상)과 같은 자리.

### 1. 메인 섹션 Right — AI Agent 운영 시스템
> **Prompt:** 16:9 aspect ratio, rounded corners. A futuristic illustration of an AI-powered pig farm operations system, designed to fit inside a card container on a website. Center: a glowing AI brain icon connected to a holographic dashboard showing abstract PSY/FCR charts. Left of center: small stylized farm building with green data streams flowing into the AI. Right of center: action output icons — dollar sign (revenue up), downward arrow (mortality down), grain (feed optimized). Composition weighted to center, with comfortable padding on all sides. Clean minimal SaaS marketing style. Dark navy (#0F172A) background with subtle grid. Emerald green (#0D7C66) data streams, gold (#C9A84C) accents on outcomes. No text. No border.

### 2. 마켓플레이스 섹션 Right — 데이터 장터
> **Prompt:** 16:9 aspect ratio, rounded corners. An illustration of a data marketplace ecosystem designed for a website card. Center: a glowing hexagonal hub. Left: 3 small farm nodes sending green data streams into the hub, each with a tiny AI agent robot icon. Right: 3 corporate nodes (grain icon for feed company, DNA helix for genetics, molecule for pharma) receiving gold data streams from the hub. AI agent icons travel along the lines carrying data packets. Compact composition fitting cleanly within the card frame. Dark navy (#0F172A) background. Green (#0D7C66) for farm data flows, gold (#C9A84C) for business insight flows. Futuristic but clean. No text. No border.

### 3. 대안 — 데이터→AI→Action 수평 플로우
> **Prompt:** 16:9 aspect ratio, rounded corners. A horizontal three-stage flow illustration for a website card. Stage 1 (left third): farm building icon with small data dots floating up. Stage 2 (center third): a glowing AI Agent hexagon with neural patterns processing the data. Stage 3 (right third): three small output icons — calendar, alert bell, coin stack — representing scheduled actions, warnings, and revenue. Thin glowing lines connect all three stages left to right. Data particles transform from green (raw) to gold (processed) as they flow. Dark navy (#0F172A) background, emerald green (#0D7C66) and gold (#C9A84C). Compact, fits within card container. No text. No border.

### 4. 대안 — SaaS vs AI 비교
> **Prompt:** 16:9 aspect ratio, rounded corners. A split-screen comparison for a website card. Left half (dimmer, muted blue-gray): traditional SaaS icons — clipboard, spreadsheet, manual input, static charts. Right half (vibrant, glowing): AI system icons — brain/agent icon, automated dashboard, real-time data streams, revenue coins flowing. A subtle arrow transition from left to right in the center. Right side radiates energy, left side is static and faded. Clean illustration style. Fits within rounded card container. No text. No border.

---

## 컴포넌트 배치

```
pigplan/page.tsx:

<PageHero namespace="pages.pigplan" />
<PigPlanSection showHeader={false} />         ← 기존 피그플랜
<PigPlanCoreSection />                        ← 새로 추가
<PartnerMarquee />
<InsightPigPlanSection />
<PigSignalSection />
```

PigPlanCoreSection은 기존 PigPlanSection / InsightPigPlanSection과 **동일한 레이아웃**:
- `<Section>` 컴포넌트
- `grid lg:grid-cols-2 gap-16 items-center`
- Left: 텍스트 (label + title + desc + features)
- Right: 이미지 (`aspect-video rounded-2xl overflow-hidden` — 위 프롬프트 이미지)
- Stats: 기존 StatCard 컴포넌트 재활용 (4개: 5개 시장 / 7개 언어 / AI Agent / 성과 기반)
- CTA: Button 컴포넌트 (자세히 보기 + 프로토타입 보기)
