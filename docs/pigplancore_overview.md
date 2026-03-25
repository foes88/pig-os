# PigPlanCORE

> Global Swine Farm Management SaaS Platform

---

## Overview

PigPlanCORE is a cloud-based swine farm management platform designed for mid-to-large scale pig farms (500~5,000 sows) worldwide. Built on 27 years of domain expertise in swine production, the platform provides breeding cycle management, KPI dashboards, global benchmarking, and AI-powered analytics — starting completely free.

---

## What We Do

- **Breeding Cycle Management** — Mating, farrowing, weaning records with full sow history tracking
- **KPI Dashboard** — PSY, NPD, FCR, farrowing rate with real-time monitoring
- **Global Benchmarking** — Compare your farm performance against regional and global averages
- **Multi-farm Management** — Manage multiple farm sites from a single account
- **Multi-language** — English, Chinese, Vietnamese, Thai, Korean, Brazilian Portuguese, LATAM Spanish
- **6-Level Access Control** — Group Admin / Farm Owner / Manager / Veterinarian / Worker / Viewer
- **Reports** — Monthly KPI, breeding performance, mortality, shipment analytics

---

## Target Market

**Core Target: 500~5,000 sow mid-to-large farms**

The top 40 companies own just 26% of global sows. The remaining 74% — mid-size farms growing from 500 to 5,000 sows — are the most underserved segment in swine management software.

### 5 Markets

| Market | Focus | Characteristics |
|--------|-------|----------------|
| **USA** | Benchmarking + Feed Mill integration | Established industry, high ARPU |
| **China** | Large-scale management + price volatility | Rapid consolidation, mega farms emerging |
| **Southeast Asia** (Vietnam, Thailand) | Product-driven growth | Greenfield market, no dominant SaaS competitor |
| **Latin America** | Integrator-contract farm structure | Agriness dominates Brazil, opportunity elsewhere |
| **South Korea** | Reference market | Proven domain expertise, fast tech adoption |

---

## Why PigPlanCORE

### Market Gap

No single competitor satisfies all five of these simultaneously:

1. **SME-optimized** — Enterprise tools are too expensive and complex for mid-size farms
2. **Free entry** — All competitors charge $500+/year or hide pricing entirely
3. **Open API** — PigKnows and PigCHAMP have no open API
4. **IoT + Sow management in one** — Currently split across separate products
5. **AI for all farms** — Currently available only for enterprise-scale operations

### Competitive Landscape

9 competitors analyzed across North America, Europe, and Latin America:

| Competitor | Market | Pricing |
|-----------|--------|---------|
| PigKnows (Valstone) | US → Global | Undisclosed |
| PigCHAMP | US/CA/LatAm | Undisclosed |
| MetaFarms | US | ~$0.05-0.25/pig shipped |
| Cloudfarms (BASF) | EU, 24 languages | From $500/year |
| Agriness | Brazil (90% share) | Freemium |
| MTech Systems | US/EU Enterprise | Undisclosed |
| Porcitec | EU (Spain) | Undisclosed |
| LeeO | EU (Denmark, IoT) | Undisclosed |
| S&W | EU (Denmark) | Undisclosed |

---

## Technology

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | FastAPI (Python) | AI/ML native ecosystem. Java migration when scale demands |
| Frontend | Next.js + TypeScript | |
| Mobile | Android Native + iOS Native | |
| Database | PostgreSQL (Schema-per-tenant) | Complete data isolation per farm. Scales to thousands of farms |
| Time-series | TimescaleDB | IoT sensor data. 979x faster aggregation than standard PostgreSQL |
| Infrastructure | AWS or GCP | Southeast Asia regions available |

### Architecture Principles

- **Schema-per-tenant** — Each farm's data is completely isolated. Scalable to 5,000+ farms via Citus sharding
- **Modular design** — 49 tables across 11 modules, independently deployable per phase
- **5-market localization** — Single schema handles all regions via country_configs (units, currency, date format, messaging)
- **Audit trail** — All data changes logged for compliance

---

## Business Model

### Phase 1: Free

All features free. User acquisition + data collection + market validation.

### Phase 2+: Tiered Pricing (TBD)

Sow count-based pricing tiers under development:

| Tier | Pricing |
|------|---------|
| Under 200 sows | Free |
| 200~5,000 sows | Tiered (TBD) |
| 5,000+ sows | Custom negotiation |

*Multi-farm management for integrators available as separate paid module.*

### B2B Data Revenue

Aggregated, anonymized farm data sold to feed companies, genetics firms, and pharmaceutical companies as benchmarking and market intelligence products.

**Validation:** Cargill's strategic investment in Agriness (2M+ sows, Brazil) confirms willingness to pay for swine performance data.

---

## Go-to-Market

**Principle: We don't sell directly. We build a structure that spreads and gets chosen.**

1. **Product sells itself** — Free usage proves value
2. **Users spread it** — Veterinarians and consultants recommend naturally + referral incentives
3. **Content builds trust** — Benchmarks and reports prove expertise

### By Market

| Market | Strategy | Key |
|--------|----------|-----|
| Vietnam / Thailand | Product-driven | "Get mass usage" |
| USA / China / LatAm / Korea | Content-driven | "Build trust, receive inquiries" |

### Key Channels (Near-zero cost)

- Free benchmark report (sign up = see your PSY ranking)
- Swine community activity (Facebook/Zalo groups)
- Veterinarian free accounts (1 vet = dozens of farms)
- Referral incentives
- Industry site contributions (pig333.com, ThePigSite)
- SEO / content marketing

---

## Development Status

| Item | Status |
|------|--------|
| DB Schema | 49 tables, 11 modules — Complete |
| API Spec | 30 endpoints — Complete |
| KPI Formulas | PSY, NPD, FCR, Farrowing Rate — Complete |
| Master Data | 48 event types, 30 diseases, 22 vaccines, 22 antibiotics — Complete |
| UI Prototypes | 13-page full version + 4-page lite version — Complete |

### Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Web | 8 weeks | Design (2wk) + Dev (3wk) + Test/Launch (3wk) |
| Mobile | 10 weeks after web | Android Native (6wk) + iOS + Test/Beta (4wk) |

---

## Links

- [Global Strategy Report (v2)](https://foes88.github.io/PigplanCORE/docs/meeting-prep/2026-03-23_CORE_Meeting2_Prep_v2.html)
- [MVP Prototype (Full)](https://foes88.github.io/PigplanCORE/mvp/)
- [MVP Prototype (Lite)](https://foes88.github.io/PigplanCORE/mvp-lite/)
- [UI Concepts (5 designs)](https://foes88.github.io/PigplanCORE/concepts/index.html)
- [Strategy Deep Dive (Q1~Q3)](https://foes88.github.io/PigplanCORE/docs/presentations/2026-03-23_Strategy_Deep_Dive.html)

---

*PigPlanCORE — Built on 27 years of swine expertise. Designed for the world.*
