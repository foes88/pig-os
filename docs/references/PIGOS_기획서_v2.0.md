# PigOS — 통합 기획서 v2.0
<!-- Last updated: 2026-03-27 -->
<!-- 병합 기준: references/ 8개 파일 + 전략 전환 논의 (2026.03.24~27) -->
<!-- 변경 표기: ⚡ Updated / ✨ New / ~~삭제~~ -->

---

## 변경 이력

| 버전 | 날짜 | 주요 변경 |
|------|------|-----------|
| v1.0 | 2026.03.19 | 초기 기획 (PigOS, SaaS 모델) |
| v2.0 | 2026.03.27 | PigOS 전환, AI Agent 구조, 과금 모델 재정의 |

---

## 목차

1. [Executive Summary](#1-executive-summary)
2. [전략 전환 배경](#2-전략-전환-배경--saaspocalypse-대응)
3. [제품 정의 — 4가지 전환](#3-제품-정의--4가지-전환)
4. [기술 아키텍처](#4-기술-아키텍처)
5. [AI Agent 설계](#5-ai-agent-설계)
6. [비즈니스 모델 및 과금 구조](#6-비즈니스-모델-및-과금-구조)
7. [MVP 로드맵](#7-mvp-로드맵)
8. [온보딩 UX 설계](#8-온보딩-ux-설계)
9. [글로벌 시장 분석](#9-글로벌-시장-분석)
10. [경쟁사 분석 및 포지셔닝](#10-경쟁사-분석-및-포지셔닝)
11. [파일럿 전략](#11-파일럿-전략)
12. [중장기 확장 전략](#12-중장기-확장-전략)
13. [투자자 피치 내러티브](#13-투자자-피치-내러티브)
14. [인프라 및 운영 결정](#14-인프라-및-운영-결정)
15. [오픈 질문 및 다음 액션](#15-오픈-질문-및-다음-액션)

---

## 1. Executive Summary

### ⚡ Updated: 제품 정의

**PigOS**는 AI Agent 기반의 양돈 운영 최적화 시스템이다.  
기존 양돈 관리 SaaS가 "기록하는 시스템"이라면, PigOS는 **"농장의 수익을 직접 증가시키는 시스템"**이다.

핵심 전환:

```
기존: 양돈 관리 SaaS (PigOS)
         ↓ 데이터 기록 → 리포트 → 농장주가 판단
         
신규: AI 기반 양돈 운영 최적화 시스템 (PigOS)
         ↓ 데이터 → AI Agent → 행동 지침 → 수익 개선
```

### 생존 기준

> **"이 시스템이 농장의 수익을 직접 증가시키는가?"**

### 3줄 요약

- **Farm OS 무료**: 진입 장벽 제거, 피그플랜 700+ 농장 데이터 시드 활용
- **AI Agent 과금**: NPD 손실 감지·행동 스케줄러·이상 감지 등 usage/outcome 기반
- **생태계 수익**: 공급업체·금융기관·도축장이 농장 데이터 파이프라인 접근에 비용 지불

---

## 2. 전략 전환 배경 — SaaSpocalypse 대응

### 2.1 시장 변화

글로벌 SaaS 시장은 AI 대체로 구조적 위기를 맞고 있다.  
기존 양돈 SW(PigCHAMP·PigKnows)는 "400개 필터·데이터 시각화"를 제공하지만, 농장주는 돈사에서 돼지를 봐야 한다. **분석할 시간이 없다.**

| 구조 | 기존 SaaS | AI Native |
|------|-----------|-----------|
| 산출물 | 숫자·차트·리포트 | 행동 지침 + 자동 실행 |
| 사용자 역할 | 관리자 (판단·실행) | 감독자 (승인·예외 처리) |
| 가치 측정 | 기능 수 | 수익 개선 금액 |
| 과금 기준 | Per-seat | Usage / Outcome |

### 2.2 경쟁 구도 변화

- **Valstone의 PigKnows 인수 (2025.6)**: 북미 1위 SW 인수, 폐쇄형 수직통합 심화 예고
- **Agriness (브라질)**: 라틴아메리카 90% 점유, Cargill 투자 유치
- **PigCHAMP**: 40년 레거시, API 없음, 구식 UI — 전환 기회

### 2.3 PigOS의 역공 전략

PigKnows·PigCHAMP가 **폐쇄형**으로 가는 사이,  
PigOS는 **오픈 생태계**로 간다.

---

## 3. 제품 정의 — 4가지 전환

### ⚡ Updated

| 항목 | 기존 (v1.0) | 신규 (v2.0) |
|------|-------------|-------------|
| **제품명** | PigOS | **PigOS** |
| **제품 정의** | 양돈 관리 SaaS | AI 기반 양돈 운영 최적화 시스템 |
| **기술 구조** | CRUD 중심 SaaS | Event + Time-series + Agent + Workflow |
| **과금 모델** | Per-farm 구독 | Platform 무료 + Agent usage/outcome + Marketplace |
| **투자 포지셔닝** | Agri SaaS | **Vertical AI for Pig Farm Operations** |

### ✨ New: 핵심 포지셔닝 문장

```
PigCHAMP: "400개 필터를 드립니다" → 농장주가 분석
PigOS: "오늘 할 일 3가지를 드립니다" → AI가 분석, 농장주가 실행
```

---

## 4. 기술 아키텍처

### 4.1 전체 구조 (기존 확정 스택 유지)

```
┌─────────────────────────────────────────────┐
│           출력 레이어 (Output Layer)          │
│  웹 대시보드 (Next.js + TypeScript)           │
│  모바일 앱 (React Native)                    │
│  Open API / Webhook                          │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│      ✨ AI Agent 레이어 (신규 추가)           │
│  Agent 1: 손실 감지 (규칙 기반, Day 1)       │
│  Agent 2: 행동 스케줄러 (캘린더 자동화)       │
│  Agent 3: 이상 감지 (±20% 알림)             │
│  [Phase 2] ML 기반 예측 고도화               │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         백엔드 레이어 (Backend Layer)         │
│  FastAPI (Phase 1) → Java Spring Boot (Phase 2)│
│  Redis: 캐시 + 알림 큐                       │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         데이터 레이어 (Data Layer)            │
│  PostgreSQL: 개체·농장 데이터                 │
│  TimescaleDB: IoT 시계열 데이터               │
│  Schema-per-tenant 멀티테넌시                 │
│  Oracle MCP 분석 → ETL 마이그레이션           │
└─────────────────────────────────────────────┘
```

### 4.2 기술 스택 결정 (변경 없음)

| 레이어 | Phase 1 (MVP) | Phase 2 (스케일업) |
|--------|---------------|-------------------|
| 백엔드 | FastAPI (Python) | Java Spring Boot |
| 프론트 | Next.js + TypeScript | 동일 |
| 모바일 | React Native | 동일 |
| DB | PostgreSQL + TimescaleDB | + Citus (5,000농장+) |
| 캐시/알림 | Redis | 동일 |
| 멀티테넌시 | Schema-per-tenant | Schema-based Sharding |
| 오프라인 | WatermelonDB | 동일 |
| 클라우드 | AWS 싱가포르 or GCP | 재평가 |

> **FastAPI 선택 근거**: MVP 개발 속도 최우선 + Python AI/ML 생태계 활용.
> API 계약(엔드포인트·스키마) 유지 시 내부 구현체 교체 가능.

### 4.3 멀티테넌시: Schema-per-tenant

```
농장 수      상태          대응
~500개      문제없음       기본 PostgreSQL 충분
500~2,000   양호          PgBouncer Transaction Pooling 필수
2,000~5,000 주의          카탈로그 최적화 + 커넥션 관리 강화
5,000개+    전환 검토      Citus 12 Schema-based Sharding
```

확장 경로: Schema-per-tenant → Citus 12 (기존 스키마 유지하며 수평 확장 가능)

### 4.4 핵심 DB 스키마 (Agent 레이어 포함)

```sql
-- ── 공통: 농장 (Farm OS 기반) ──
CREATE TABLE farms (
    farm_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    country_code    CHAR(2) NOT NULL DEFAULT 'KR',
    daily_sow_cost  NUMERIC(10,2),     -- NULL이면 국가 기본값 사용
    currency        CHAR(3) DEFAULT 'KRW',
    unit_system     VARCHAR(10) DEFAULT 'METRIC',
    timezone        TEXT DEFAULT 'Asia/Seoul',
    language        VARCHAR(5) DEFAULT 'ko',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 모돈 개체 ──
CREATE TABLE sows (
    sow_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id     UUID REFERENCES farms(farm_id),
    ear_tag     TEXT NOT NULL,
    parity      INT DEFAULT 0,
    status      TEXT DEFAULT 'ACTIVE',  -- ACTIVE/PREGNANT/LACTATING/DRY/CULLED
    entry_date  DATE,
    UNIQUE(farm_id, ear_tag)
);

-- ── 생산 이벤트 (Event-driven) — TimescaleDB hypertable ──
CREATE TABLE production_events (
    event_id    UUID DEFAULT gen_random_uuid(),
    sow_id      UUID REFERENCES sows(sow_id),
    farm_id     UUID REFERENCES farms(farm_id),
    event_type  TEXT NOT NULL,  -- SERVICE/PREG_CHECK/FARROWING/WEANING/CULL
    event_date  DATE NOT NULL,
    litter_size INT,
    born_alive  INT,
    stillborn   INT DEFAULT 0,
    notes       TEXT,
    -- 오프라인 동기화
    offline_created_at  TIMESTAMPTZ,
    synced_at           TIMESTAMPTZ,
    sync_conflict       BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
-- SELECT create_hypertable('production_events', 'event_date');

-- ✨ Agent 1 결과 캐시 ──
CREATE TABLE loss_reports (
    report_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID REFERENCES farms(farm_id),
    report_date     DATE NOT NULL,
    total_loss      NUMERIC(15,2),
    monthly_loss    NUMERIC(15,2),
    top_actions     JSONB,
    detail          JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ✨ Agent 2 스케줄 캐시 ──
CREATE TABLE scheduled_actions (
    action_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID REFERENCES farms(farm_id),
    sow_id          UUID REFERENCES sows(sow_id),
    action_type     TEXT,   -- PREG_CHECK/FARROWING_PREP/WEANING/RESERVICE
    due_date        DATE NOT NULL,
    sent_push       BOOLEAN DEFAULT FALSE,
    completed       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 사료 이상 감지용 시계열 (Agent 3 준비) ──
CREATE TABLE feed_records (
    record_id       UUID DEFAULT gen_random_uuid(),
    farm_id         UUID REFERENCES farms(farm_id),
    barn_id         TEXT,
    recorded_at     TIMESTAMPTZ NOT NULL,
    feed_amount_kg  NUMERIC(8,2),
    water_intake_l  NUMERIC(8,2)
);
-- SELECT create_hypertable('feed_records', 'recorded_at');
```

### 4.5 국가별 특화 스키마 (기존 분석 유지)

```sql
-- 한국: mtrace + 임신돈 군사 전환
ALTER TABLE farms ADD COLUMN mtrace_id VARCHAR(20);
ALTER TABLE sows ADD COLUMN stall_to_group_converted BOOLEAN;

-- EU: SPF + 항생제 DDDA + 동물복지
ALTER TABLE farms ADD COLUMN spf_status VARCHAR(20);
CREATE TABLE antibiotic_usage (
    id UUID PRIMARY KEY,
    farm_id UUID REFERENCES farms(farm_id),
    usage_date DATE,
    mg_animal_biomass DECIMAL(10,6),  -- EU ESVAC 지표
    ddda_value DECIMAL(10,6),          -- 덴마크 지표
    vfd_number VARCHAR(50)             -- 미국 VFD
);

-- 미국: Prop 12 + 락토파민
ALTER TABLE farms ADD COLUMN prop12_compliant BOOLEAN;
ALTER TABLE sows ADD COLUMN ractopamine_free BOOLEAN;

-- 동남아: ASF 백신 + 오프라인 + 소농 모드
CREATE TABLE asf_vaccine_records (
    id UUID PRIMARY KEY,
    farm_id UUID REFERENCES farms(farm_id),
    vaccine_name VARCHAR(100),  -- NAVET-ASFVAC / AVAC ASF LIVE / DACOVAC-ASF2
    vaccination_date DATE,
    next_due_date DATE
);
ALTER TABLE farms ADD COLUMN farm_scale VARCHAR(10); -- COMMERCIAL/SMALL/BACKYARD
```

---

## 5. AI Agent 설계

### ⚡ Updated: Agent 철학

```
❌ 하면 안 되는 것: AI 리포트, AI 챗봇, 추천 기능 → "보조 기능"
✅ 해야 할 것:      데이터 → AI Agent → 행동(Action) 자동화
```

### 5.1 Agent 1 — 손실 감지 (MVP 필수)

**작동 방식**: 규칙 기반, 벤치마크 불필요, **Day 1 작동**

```python
# 생물학적 상수 (전 세계 공통)
GESTATION_DAYS = 114       # 임신 기간
OPTIMAL_WEI_TO_SERVICE = 5 # 이유 후 최적 재교배일

# 손실 계산 로직
NPD 손실 = (현재일 - 이유일 - 5일) × 일당 유지비
           (이유 후 5일 초과 모돈만 해당)

분만 지연 손실 = (현재일 - 교배일 - 114일) × 일당비 × 1.5
                (교배일+114일 초과 미분만 개체만)
```

**국가별 일당 유지비 기본값**:

| 국가 | 기본값 | 통화 |
|------|--------|------|
| 한국 | 8,500 | KRW |
| 베트남 | 45,000 | VND |
| 미국 | 2.80 | USD |
| EU | 2.50 | EUR |

> 온보딩에서 사용자 직접 입력 시 override 가능

**아하 모먼트 출력 예시**:
```
현재 이 농장에서 놓치고 있는 돈: ₩2,688,000
─────────────────────────────────
· NPD 42일 모돈 8두 → ₩2,016,000 손실 진행 중
· 분만 지연 모돈 2두 → ₩672,000 손실 진행 중

이번 달 미조치 시 추가 예상 손실: ₩7,200,000
```

### 5.2 Agent 2 — 행동 스케줄러 (MVP 필수)

**작동 방식**: 교배일 입력 → 자동 캘린더 생성 + 푸시 알림

```
교배일 입력
    ├── 임신 확인일:    +25일    → D-3일 푸시 알림
    ├── 분만 예정일:    +114일   → D-1일 푸시 알림
    ├── 이유 예정일:    분만+21일 → D-1일 푸시 알림
    └── 재교배 예정일:  이유+5일  → 당일 푸시 알림
```

**메인 대시보드 출력**:
```
오늘 확인해야 할 모돈 (3마리)
┌────────────────────────────────────────┐
│ 모돈 #042  분만 예정일 D-1  → 분만사 준비 확인 │
│ 모돈 #018  이유 후 7일 경과 → 즉시 재교배 필요 │  
│ 모돈 #055  임신확인 예정   → 오늘 임신 확인  │
└────────────────────────────────────────┘
```

### 5.3 Agent 3 — 이상 감지 (MVP+ 2주차)

**작동 방식**: 자기 농장 평균 대비 ±20% 이상 시 알림 (ML 불필요)

```python
# 이상 임계값: 자기 농장 최근 90일 평균 기준
사료 섭취량 이상: current_feed > avg_feed * 1.20 or < avg_feed * 0.80
체중 증가 이상:  current_gain < expected_gain * 0.80
폐사율 이상:    current_mortality > rolling_avg * 1.50
```

> Phase 2에서 Federated Learning 기반 ML 모델로 고도화

### 5.4 AI 기능 벤치마크 의존성 분석

| AI 기능 | 벤치마크 필요 | 작동 방식 |
|---------|:------------:|-----------|
| 분만 예정일 경보 | ❌ | 교배일 + 114일 ± 3일 |
| NPD 손실 계산 | ❌ | 이유일 ~ 현재일 × 일당비용 |
| 도태 추천 | ❌ | 산차 + 최근 3회 산자수 하락 추이 |
| 행동 스케줄러 | ❌ | 돈군 상태 기반 일정 생성 |
| 사료 이상 감지 | ❌ | 자기 농장 평균 ±20% |
| PSY 트렌드 | ❌ | 자기 농장 월별 추이 (Strava 모델) |
| 최적 교배 타이밍 | ❌→⬆ | 초기: 이유+4~6일 규칙 → 데이터 쌓이면 개체별 패턴 |
| 국가별 벤치마크 | ✅ | 국가 50+ 농장 달성 시 자동 활성화 |

**→ AI 기능 87.5%는 벤치마크 없이 Day 1부터 작동 가능**

---

## 6. 비즈니스 모델 및 과금 구조

### ⚡ Updated: 3단계 수익 모델

```
1단계: Farm OS (완전 무료)
   목적: 사용자 기반 확보, 피그플랜 700+ 농장 시드 활용
   경쟁사: 전부 유료($500+/년) → PigOS는 무료 → 시도 장벽 완전 제거

2단계: AI Agent 과금 (usage / outcome)
   Usage 기반: 질병 예측 1회당 / 출하 최적화 실행당 / 분석 호출량
   Outcome 기반: 폐사율 2% 감소 → 수익 쉐어 X%
                 사료 효율 개선 → 성과 기반 과금

3단계: B2B 데이터 API (생태계 수익)
   공급업체(사료·동물약품·장비): 농장 파이프라인 접근 비용
   도축장·가공업체: 출하 타이밍 데이터 연동
   금융·보험기관: AI 성과 기반 상품 설계 데이터
   → 농장은 무료 노드, 생태계 참여자들이 지불
```

### 지역별 과금 방향

| 지역 | Basic /sow/월 | Pro /sow/월 | 비고 |
|------|:-------------:|:-----------:|------|
| SEA | $0.01~0.02 | $0.03~0.05 | + ASF 모듈 |
| 한국 | $0.02~0.04 | $0.04~0.08 | + mtrace 연동 |
| EU | $0.04~0.08 | $0.06~0.10 | + 규정 모듈 |
| 미국 | $0.05~0.10 | $0.08~0.15 | + Feed 연동 |

> Phase 2 유료 전환 시 **투명 공개** — 경쟁사는 전부 비공개, PigOS만 공개

### 결제 인프라 결정

```
초기: Stripe (수수료 2.9%+$0.30, 한국 법인 직접 연동, 개발 쉬움)
전환: Paddle (세금·규정 전부 Paddle 처리, 글로벌 판매 간편)

흐름: 글로벌 농장주 → Stripe/Paddle 카드 결제 → 4일 후 한국 법인 계좌 입금
     → 미국 법인 별도 설립 불필요
```

---

## 7. MVP 로드맵

### ⚡ Updated: 4주 스프린트 (기존 8주 → 4주 우선 검증)

```
Week 1 — Oracle MCP 분석 + ETL 설계
  □ Oracle MCP로 핵심 테이블 10개 구조 파악
    - SOW / MATING / FARROWING / WEANING / FARM
  □ 재사용 가능 엔티티 확인 (모돈·교배·분만·이유)
  □ PostgreSQL 스키마 초안 확정
  □ FastAPI 프로젝트 생성 + 기본 인증 API

Week 2 — Agent 1 + Agent 2 구현
  □ Agent 1: NPD 손실 계산 엔진 (규칙 기반)
  □ Agent 1: 분만 지연 손실 계산
  □ Agent 2: 교배일 기반 자동 캘린더 생성
  □ Redis 알림 큐 연결
  □ 국가별 일당비용 기본값 적용

Week 3 — 웹 대시보드 + 모바일
  □ 메인 화면: 손실 금액(상단) + 오늘 할 일(중단) + 추이(하단)
  □ React Native 모바일 앱
  □ 푸시 알림 (분만·이유·재교배 D-1)
  □ Agent 3: 사료 이상 감지 (간이 버전)
  □ 한국어·영어·베트남어 i18n

Week 4 — 파일럿 농장 실증
  □ 파일럿 농장 1곳 데이터 파이프 연결
  □ Agent 작동 검증 (손실 계산 정확도 확인)
  □ 농장주 피드백 수집
  □ 성공 기준 달성 여부 판정
```

**성공 기준 (4주 후)**:
- Agent 손실 계산 정확도: 농장주 "이 숫자 맞다" 확인
- 행동 지침 실행률: 50% 이상
- 일일 앱 오픈율: 70% 이상
- Agent가 잡아낸 실제 손실 케이스: 최소 3건 문서화

---

## 8. 온보딩 UX 설계

### 핵심 원칙: 5분 안에 아하 모먼트

```
Step 1 (1분)  국가 선택 + 모돈 수 입력
                  ↓
Step 2 (2분)  모돈 귀표번호 + 이유일 입력 (필수 2개만)
              * 교배일·산차는 선택 — 나중에 채워도 됨
                  ↓
Step 3 (즉시) 아하 모먼트 화면
              ┌──────────────────────────────────┐
              │  현재 이 농장에서 놓치는 돈        │
              │  ₩2,688,000                      │
              │                                  │
              │  오늘 할 일                       │
              │  1. 모돈 #018 즉시 재교배 확인    │
              │  2. 모돈 #042 분만사 준비 (D-1)  │
              │  3. 모돈 #033 임신 확인 예정      │
              └──────────────────────────────────┘
                  ↓
메인 대시보드 (영구 사용)
```

**3가지 UX 원칙**:
1. **입력 최소화**: 이유일 1개만으로 첫 손실 계산 → 나머지 점진적 수집
2. **돈 먼저**: 기능 소개 없음, 첫 화면 = 손실 금액
3. **행동 중심**: 차트·필터 없음, "지금 뭘 해야 하는가"만

**데이터 수집 단계**:

| 단계 | 수집 항목 | 활성화 기능 |
|------|----------|------------|
| Day 1 | 귀표번호 + 이유일 + 국가 | 손실 계산 + 아하 모먼트 |
| Week 1~4 | 교배일 + 분만일 + 산자수 | 캘린더 자동화 + 도태 추천 |
| 1개월+ | 자동 축적 | 자기 농장 PSY 추이 + 이상 감지 베이스라인 |
| 6개월+ | 국가 50+ 농장 | 국가별 벤치마크 자동 활성화 |

---

## 9. 글로벌 시장 분석

### 9.1 지역별 생산성 현황

| 지역 | PSY 평균 | FCR | 최대 리스크 | 주요 규정 | 진입 순서 |
|------|:--------:|:---:|-------------|-----------|:---------:|
| 동남아 | 10~26두 | 2.4~4.5 | ASF 재조합 변이 | 오프라인 필수 | **1순위** |
| 한국 | 21.9두 | 3.26~3.3 | ASF+군사전환 | mtrace 의무 | 2순위 |
| 미국 | 25.1두 | 2.5~3.0 | PRRS+Prop 12 | VFD 의무 | 3순위 |
| 브라질 | 29~32두 | 2.3~2.6 | 수출규제 | GTA 의무 | 장기 |
| EU(덴마크) | 35.6두 | 2.38 | 환경규제 | ESVAC 의무 | 장기 |
| 중국 | ~24두 | 2.63 | 돈가 변동성 | MARA 보고 | 참고용 |

> PSY 격차 최대 26두 → 단일 기준 관리 불가 → 지역별 맞춤 설계 필수

### 9.2 동남아 오프라인 수요 분석 (1순위 시장)

**오프라인 기능 필요 농가 비율**:

| 국가 | 좁은 정의 | 넓은 정의 | 비고 |
|------|:---------:|:---------:|------|
| 인도네시아 | 12~25% | 65~80% | 도서 지형, 원격지 |
| 베트남 | 10~20% | 60~75% | 시장 최대(3,200만두), 전력불안 |
| 태국 | 1~5% | 30~45% | SEA 중 인프라 최우수 |

**핵심 시사점**:
- Cloudfarms·Pig'UP·Porcitec 모두 오프라인 모드 기본 탑재 → **표준 요건**
- 4G 커버리지 ≠ 실사용 (베트남 4G 99.8% vs 농촌 실사용 70%)
- 선진국도 오프라인 수요 존재 (미국 20~30%, 한국 8~15%)
- **오프라인 기능 = 글로벌 공통 필수 사양**

**SEA 진입 우선순위**: 베트남 → 태국 → 인도네시아

### 9.3 한국 시장 특화 포인트

- **2030년 임신돈 군사 전환 의무**: 2025년 조사 기준 52.7% 농가가 기한 내 전환 불가
  → 전환 진행률 관리 모듈 → 즉시 필요
- **mtrace 연동 의무**: 출생~도축~소매 전 과정 추적
- **도체 등급 격차**: 1+ vs 2등급 두당 약 53,064원 차이 → 등급 분석 기능 수익성 명확

### 9.4 미국 시장 특화 포인트

- **PRRS 연간 손실 $6.64억** → 방역 추적 Agent 높은 가치
- **Prop 12 (2024.1 전면 시행)**: 24sqft/모돈 의무 → 준수 여부 추적
- **락토파민 수출 제한**: 160개국+ 금지 → 수출용 별도 라인 관리 필요

---

## 10. 경쟁사 분석 및 포지셔닝

### 10.1 경쟁사 핵심 약점 (우리의 기회)

| 경쟁사 | 핵심 약점 | PigOS 기회 |
|--------|----------|----------------|
| **PigKnows** | API 없음, Valstone 폐쇄형 심화 | 오픈 API → 어떤 Feed Mill SW와도 연동 |
| **PigCHAMP** | 400개 필터 → 분석 시간 없는 농장주 | AI가 분석, "오늘 할 일 3가지"만 제시 |
| **Cloudfarms** | BASF 의존 → 로드맵 불투명 | 독립 개발 + 오픈 API + 무료 |
| **MetaFarms** | 북미 전용, 한국·SEA 미진출 | 글로벌 + 다국어 + 오프라인 |
| **전 경쟁사** | 가격 비공개, 영업 미팅 필요 | 무료 진입 + 투명 가격 공개 |
| **전 경쟁사** | 영어/스페인어 중심 | 한국어·베트남어·태국어 즉시 지원 |

### 10.2 PigOS 차별화 매트릭스

| 기능 | PigKnows | PigCHAMP | Cloudfarms | MetaFarms | **PigOS** |
|------|:--------:|:--------:|:----------:|:---------:|:-------------:|
| **가격** | 비공개 | 비공개 | $500+/년 | 비공개 | **무료** |
| **5분 온보딩** | ○ | ○ | ◐ | ○ | **●** |
| **AI 행동 지침** | ✗ | ✗ | ✗ | ✗ | **●** |
| **손실 금액 즉시 계산** | ○ | ◐ | ○ | ○ | **●** |
| **오픈 API** | ✗ | ✗ | ◐ | ◐ | **●** |
| **다국어 (7개+)** | ○ | ✗ | ● | ✗ | **●** |
| **완전 오프라인** | ● | ◐ | ● | ● | **●** |
| **출시 예정 벤치마크** | ◐ (시드) | ● | ◐ | ● | ◐→● |

> ● 강함 / ◐ 보통 / ○ 약함 / ✗ 없음

---

## 11. 파일럿 전략

### 11.1 농장 선정 기준

1. **데이터 밀도**: 피그플랜 기록 월 이벤트 50건 이상
2. **규모**: 모돈 200~500두 (손실 금액 임팩트 충분 + 현장 변수 관리 가능)
3. **디지털 수용성**: 이미 피그플랜 사용 중, 스마트폰 입력 가능
4. **접근성**: 직접 방문 가능한 반경
5. **문서화 의향**: 주 1회 피드백 인터뷰 동의 가능

### 11.2 계약 구조

- **기간**: 3개월 완전 무료
- **의무**: 주 1회 피드백 인터뷰 (30분) + 성과 데이터 익명 활용 동의
- **인센티브**: 성공 시 6개월차부터 Agent 구독 전환 우선 협상권 + 케이스 스터디 공동 발행

### 11.3 성공 지표 (4주)

| 지표 | 기준 |
|------|------|
| Agent 손실 계산 정확도 | 농장주 "이 숫자가 실제랑 맞다" 확인 |
| 행동 지침 실행률 | 50% 이상 |
| 일일 앱 오픈율 | 70% 이상 |
| Agent 잡아낸 실제 손실 케이스 | 최소 3건 문서화 |

---

## 12. 중장기 확장 전략

### 12.1 기존 4대 격차 해소 (유지)

1. **멀티사이트 엔터프라이즈**: 대형 계열화 농장 본사-위탁 권한 구조
2. **사료 공급망 관리**: Feed Mill 직접 발주 연동 + 사료빈 재고 추적
3. **완전 오프라인 모바일**: WatermelonDB 기반 자동 동기화 (MVP 포함)
4. **유전/혈통 분석**: EBV 데이터 연동, 유전 회사 API 연결

### ✨ New: 5가지 확장 레이어

5. **집단지성 네트워크 (Waze for pig farms)**
   - Federated Learning: 농장 간 데이터 공유 없이 모델 가중치만 집계
   - 베트남 50곳에서 이상 패턴 감지 → 인접 농장 48시간 전 경고
   - 사용자 늘수록 모델 강해지는 플라이휠 = 진짜 해자

6. **디지털 팜 트윈**
   - "만약 모돈 50두 추가하면?" → 3개월 후 인력·사료·이익 시뮬레이션
   - 보험사·은행·바이어가 구매하고 싶어하는 B2B 데이터
   
7. **Agent 마켓플레이스 (App Store 모델)**
   - Boehringer Ingelheim → "질병 예방 특화 Agent" 판매
   - Topigs Norsvin → "유전력 최적화 Agent" 판매
   - 제3자 회사들이 농장 접근 위해 PigOS에 수수료 지불

8. **성과 연동 금융**
   - AI 성과 데이터 → 농장 "운영 신용점수" 자동 산출
   - 상위 20% 농장 → 사료 구매 대출 금리 1.5%p 우대
   - PigOS는 데이터 파이프라인 제공 + 레퍼럴 수수료 (Stripe Capital 모델)

9. **음성 우선 인터페이스**
   - "돈사 3번 사료 섭취 이상 있어" → 음성 입력 → 자동 로그 + 수의사 알림
   - 현장 작업자 핸즈프리, 다국어 지원
   - 오프라인 모바일 문제를 다른 각도에서 해결

### 12.2 콜드스타트 해결 — 유사 사례 검증

| 서비스 | 해결 방법 | PigOS 적용 |
|--------|----------|----------------|
| **Waze** | 기본 지도 제공 → 사용자 증가 시 실시간 교통 | Farm OS 제공 → 농장 증가 시 벤치마크 |
| **Strava** | "어제의 나 vs 오늘의 나" 먼저 → 세그먼트 나중 | 자기 농장 추이 먼저 → 국가 벤치마크 나중 |
| **Agriness** | 브라질 대형 인테그레이터 1곳 → 데이터 → 확산 | 피그플랜 700+ 농장 시드 데이터 활용 |

> 국가별 50+ 농장 달성 시 → "베트남 내 상위 30%입니다" 자동 알림 활성화

### 12.3 지역별 기능 우선순위

| 기능 | MVP (4주) | v1.1 (6개월) | v2 (12개월) |
|------|:---------:|:------------:|:-----------:|
| PSY/NPD/FCR KPI | ✅ 전 지역 | — | — |
| 다국어 KR/EN/VI | ✅ | — | — |
| 오프라인 Android | ✅ | + iOS | — |
| ASF 경보 | ✅ SEA | + 전 지역 | — |
| mtrace 연동 | ✅ 한국 | — | — |
| 임신돈 군사 관리 | ✅ 한국 | + EU | — |
| 항생제 보고 | — | ✅ EU | + 미국 VFD |
| Prop 12 준수 | — | ✅ 미국 | — |
| Federated Learning | — | — | ✅ |
| Agent 마켓플레이스 | — | — | ✅ |

---

## 13. 투자자 피치 내러티브

### 13.1 오프닝 훅 (15초)

> "전 세계 양돈 농장의 70%는 지금 이 순간 놓치고 있는 돈이 얼마인지 모릅니다.  
> PigOS는 데이터를 입력하는 순간 실시간으로 그 금액을 보여주고,  
> AI가 직접 돈을 회수하는 액션을 수행합니다."

### 13.2 문제 — SaaSpocalypse 맥락

- 기존 양돈 SaaS(PigCHAMP, PigKnows)는 "기록하는 도구"
- 400개 필터를 주지만 농장주는 돈사에서 돼지를 봐야 함
- AI 시대에 살아남는 제품: "정보 주는 시스템" → "돈 만들어주는 시스템"
- **SaaS = 기록 / AI = 돈**

### 13.3 솔루션

```
Farm OS (무료)          → 진입 장벽 제거
AI Agent 3종            → 운영 의사결정 자동화
오픈 API 생태계         → 제3자 참여자들이 수익원
Salesforce → Agentforce → 동일한 구조적 전환
```

### 13.4 데이터 해자 (Moat)

1. **피그플랜 700+ 농장** → 초기 벤치마크 시드 (Agriness 모델)
2. **Federated Learning 플라이휠** → 농장 늘수록 모델 강해짐
3. **오픈 API 생태계** → 전환 비용 높은 통합 구조

### 13.5 수익 역전 논리

```
기존 SaaS: 농장 → 구독료 → 우리
PigOS: 농장은 무료 노드
           공급업체·도축장·금융기관 → 파이프 접근 비용 → 우리
           
→ 농장이 많아질수록 생태계 참여자가 더 많이 지불
```

### 13.6 마일스톤

```
지금       파일럿 농장 1곳, 손실 케이스 3건 문서화
3개월      파일럿 검증 완료 → Agent 과금 모델 활성화
6개월      국가별 50+ 농장 → 벤치마크 자동 생성
12개월     글로벌 500+ 농장 → B2B 데이터 API 수익 시작
```

---

## 14. 인프라 및 운영 결정

### 14.1 클라우드

**권고: AWS 싱가포르 (기존 CLAUDE.md 명시) 또는 GCP**

| | AWS | GCP |
|--|-----|-----|
| 스타트업 크레딧 | $10K | **$200K** |
| 동남아 리전 | 싱가포르·자카르타·뭄바이 | 싱가포르·자카르타 |
| 생태계 | 가장 넓음 | 6~10% 저렴 |
| TimescaleDB | EC2 자체 설치 | VM 자체 설치 |

**전략**: GCP $200K 크레딧으로 시작 → 트래픽 증가 시 재평가

### 14.2 결제

```
초기: Stripe (수수료 2.9%+$0.30, 연동 쉬움)
전환: Paddle (글로벌 세금 처리 위임, 한국 법인 그대로)
미국 법인 설립 불필요
```

### 14.3 i18n 및 단위계

```
Phase 1: ko, en, vi
Phase 2: es, pt-BR, th  
Phase 3: zh-CN, de, fr, nl

단위계 (국가 기본값):
KR/SEA/EU/BR: METRIC (kg, ℃, ha)
US:           IMPERIAL (lb, ℉, sqft) ← 필수, 미지원 시 미국 진입 불가

통화: KRW / USD / EUR / BRL / VND / THB / PHP / IDR
```

---

## 15. 오픈 질문 및 다음 액션

### 15.1 지금 당장 결정 필요한 사항

| 질문 | 영향 | 우선순위 |
|------|------|:-------:|
| 파일럿 농장 선정 (피그플랜 내 후보 확정) | MVP 시작 가능 여부 | ★★★ |
| 국가별 일당 유지비 기본값 검증 | Agent 1 손실 계산 정확도 | ★★★ |
| Oracle MCP 분석 착수 일정 | Week 1 실행 가능 여부 | ★★★ |
| 피그플랜 700+ 농장 데이터 접근 범위 | 벤치마크 시드 활용 가능 여부 | ★★☆ |

### 15.2 중기 검토 필요 사항

- Segment C(대형 농장) 전환 전략: PigCHAMP 사용 중인 500두+ 농장이 PigOS로 전환할 동기는?
- "행동 지침" AI 정확도 검증: 도태 추천·최적 교배 타이밍의 현장 신뢰도 기준
- 무료 모델 재정적 런웨이: B2B API 수익 전환까지 충분한가?
- Agent 마켓플레이스 법적 구조: 제3자 Agent 판매 시 책임 소재

### 15.3 즉시 실행 체크리스트

```
이번 주:
  □ Oracle MCP 분석 시작 → 핵심 테이블 10개 구조 파악
  □ 파일럿 농장 후보 3곳 선정 (피그플랜 데이터 밀도 기준)
  □ FastAPI 프로젝트 생성 + PostgreSQL 로컬 환경 세팅
  □ Agent 1 손실 계산 로직 코드 리뷰 (pigops_agent1_loss_calculator.py)

2주 내:
  □ 파일럿 농장 1곳 계약 (3개월 무료 + 피드백 인터뷰 동의)
  □ Agent 1 + 2 FastAPI 엔드포인트 완성
  □ 메인 대시보드 목업 (Figma or 코드)
  □ 대표님/투자자 보고 자료 업데이트 (이 기획서 기반)
```

---

## 부록 A — 경쟁사 테스트 계정 확보

| 경쟁사 | 방법 | 비고 |
|--------|------|------|
| **PigCHAMP** | pigchamp.com Free Trial 바로 신청 | 신용카드 불필요 |
| **PigKnows** | porkcheckoff@pigknows.com 데모 요청 | 영업 담당자 연결 |
| **MetaFarms** | metafarms.com Contact Sales | 영업 프로세스 |
| **Cloudfarms** | cloudfarms.com Demo Request | BASF 계열 |
| **Agriness** | agriness.com Contact | 포르투갈어 기반 |

---

## 부록 B — 글로벌 벤치마크 기준값

```sql
-- KPI 벤치마크 초기 데이터 (references/01, 04 기반)
INSERT INTO kpi_benchmarks VALUES
  ('EU_DK',  2024, 35.6, 36.5, 31.5, 2.38, 92.0, 4),
  ('US',     2023, 25.1, 31.7, 24.5, 2.75, 78.3, 40),
  ('KR',     2023, 21.9, 32.5, 18.8, 3.28, 82.0, 42),
  ('BR',     2023, 30.0, 33.0, 27.0, 2.45, 87.0, 35),
  ('SEA_COM',2024, 23.0, 26.0, 19.0, 2.60, 80.0, 45),
  ('SEA_SML',2024, 13.0, 16.0, 11.0, 4.00, 60.0, 65);
```

---

*작성: PigOS 기획팀*  
*기반 자료: references/ 8개 파일 + 전략 전환 논의 (2026.03.24~27)*  
*다음 업데이트: Oracle MCP 분석 완료 후 + 파일럿 농장 검증 결과 반영*
