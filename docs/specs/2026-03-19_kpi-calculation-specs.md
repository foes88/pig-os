# PigOS — KPI 계산 명세서
> v1.0 · 2026.03.19
> 개발자는 이 문서의 공식과 엣지케이스를 그대로 구현할 것

---

## 1. PSY (Piglets per Sow per Year)

### 정의
모돈 1두가 연간 생산하는 이유 자돈 수

### 공식
```
PSY = SUM(weaned_count) [rolling 12개월] / AVG(active_sow_inventory)
```

### Active Sow 정의
```sql
status IN ('ACTIVE', 'GESTATING', 'LACTATING', 'WEANED', 'DRY')
AND deleted_at IS NULL
```

### 계산 방법 (Rolling 12개월)
```sql
-- 분자: 최근 12개월 이유두수 합계
SELECT SUM(w.weaned_count)
FROM weanings w
JOIN sows s ON w.sow_id = s.id
WHERE w.weaning_date >= CURRENT_DATE - INTERVAL '365 days'
  AND w.deleted_at IS NULL
  AND s.farm_id = :farm_id;

-- 분모: 일별 평균 활성 모돈수
-- 방법: 매일의 활성 모돈수를 합산 / 365
-- 간편 계산: 월초 활성 모돈수 12개월 평균
SELECT AVG(monthly_count) FROM (
    SELECT DATE_TRUNC('month', d.dt) AS month,
           COUNT(DISTINCT s.id) AS monthly_count
    FROM generate_series(
        CURRENT_DATE - INTERVAL '365 days',
        CURRENT_DATE,
        INTERVAL '1 month'
    ) d(dt)
    JOIN sows s ON s.farm_id = :farm_id
        AND s.entry_date <= d.dt
        AND (s.status NOT IN ('CULLED', 'DEAD') OR s.updated_at > d.dt)
        AND s.deleted_at IS NULL
    GROUP BY DATE_TRUNC('month', d.dt)
) sub;
```

### 엣지케이스
| 케이스 | 처리 |
|--------|------|
| 연도 중간 입식 모돈 | 분모에 존재 일수/365로 pro-rata 반영 |
| 연도 중간 폐사 모돈 | 폐사 전까지만 분모에 포함 |
| 위탁(fostering) 자돈 | **이유 모돈**에 귀속 (출산 모돈 아님) |
| 기간 내 분만 0건 | PSY = 0 (NULL 아님) |
| 활성 모돈 0두 | PSY = NULL + 경고 플래그 |
| 데이터 누락 (이유 미기록) | data_quality.completeness 경고 표시 |

### 벤치마크 비교
```json
{
  "value": 23.4,
  "benchmark_national": 21.9,
  "benchmark_top10": 32.5,
  "percentile": 65,
  "trend_vs_last_month": 0.8,
  "status": "GREEN"
}
```
- GREEN: >= benchmark_national
- YELLOW: benchmark_national × 0.9 ~ benchmark_national
- RED: < benchmark_national × 0.9

---

## 2. MSY (Marketed pigs per Sow per Year)

### 정의
모돈 1두가 연간 출하하는 비육돈 수

### 공식
```
MSY = SUM(shipped_count) [rolling 12개월] / AVG(active_sow_inventory)
```
또는 간편 계산:
```
MSY = PSY × (1 - post_weaning_mortality_rate)
```

### 데이터 소스
```sql
SELECT SUM(s.head_count)
FROM shipments s
WHERE s.farm_id = :farm_id
  AND s.shipment_date >= CURRENT_DATE - INTERVAL '365 days'
  AND s.destination_type IN ('SLAUGHTERHOUSE', 'WET_MARKET', 'EXPORT');
```

---

## 3. NPD (Non-Productive Days)

### 정의
모돈이 임신도 포유도 아닌 비생산 일수

### 공식 (모돈 개체별)
```
NPD = 이유~재교배 간격 합계 (rolling 12개월)

개별 NPD 이벤트 = next_mating_date - weaning_date (일)
연간 NPD = SUM(individual NPD events)
```

### 구성 요소
```
비생산일 = 이유~발정 대기 + 발정~교배 + 재발정 대기(임신 실패 시)

정상 사이클: 이유 → 5~7일 → 교배 → 임신확인(+) → 분만
실패 사이클: 이유 → 교배 → 임신확인(-) → 재발정 → 재교배
              이 전체 기간이 NPD에 포함
```

### SQL 구현
```sql
SELECT
    s.id AS sow_id,
    s.ear_tag,
    SUM(
        CASE
            WHEN m.mating_date IS NOT NULL AND w.weaning_date IS NOT NULL
            THEN GREATEST(0, m.mating_date - w.weaning_date)
            ELSE 0
        END
    ) AS npd_days_12m
FROM sows s
LEFT JOIN weanings w ON w.sow_id = s.id
    AND w.weaning_date >= CURRENT_DATE - INTERVAL '365 days'
    AND w.deleted_at IS NULL
LEFT JOIN LATERAL (
    -- 이유 후 가장 가까운 다음 교배를 찾음
    SELECT mating_date
    FROM matings m2
    WHERE m2.sow_id = s.id
      AND m2.mating_date > w.weaning_date
      AND m2.mating_date <= w.weaning_date + INTERVAL '60 days'
      AND m2.deleted_at IS NULL
    ORDER BY m2.mating_date ASC
    LIMIT 1
) m ON TRUE
WHERE s.farm_id = :farm_id
  AND s.deleted_at IS NULL
GROUP BY s.id, s.ear_tag;
```

### 엣지케이스
| 케이스 | 처리 |
|--------|------|
| 이유 후 재교배 안 함 (60일 초과) | NPD 60일 cap + "extended_npd" 플래그 |
| 임신확인 음성 → 재교배 | 이유~최종 성공 교배까지 전체 NPD |
| 초산 미경산돈(gilt) | entry_date부터 첫 교배까지가 NPD |
| 이유 기록 누락 | data_quality 경고, 해당 사이클 제외 |

### 목표값
| 지역 | 목표 | 우수 |
|------|------|------|
| KR | <40일 | <35일 |
| US | <45일 | <38일 |
| EU(DK) | <38일 | <32일 |

---

## 4. Farrowing Rate (분만율)

### 정의
교배한 모돈 중 실제 분만에 성공한 비율

### 공식
```
분만율(%) = (분만 모돈수 / 교배 모돈수) × 100

코호트 방식:
- 교배일 기준 110~150일 전 교배 건 대상
- 해당 교배 건 중 분만 기록이 있는 비율
```

### SQL 구현
```sql
SELECT
    COUNT(DISTINCT m.id) AS total_mated,
    COUNT(DISTINCT f.id) AS total_farrowed,
    ROUND(
        COUNT(DISTINCT f.id)::DECIMAL / NULLIF(COUNT(DISTINCT m.id), 0) * 100
    , 1) AS farrowing_rate_pct
FROM matings m
LEFT JOIN farrowings f ON f.mating_id = m.id AND f.deleted_at IS NULL
LEFT JOIN sows s ON m.sow_id = s.id
WHERE m.farm_id = :farm_id
  AND m.mating_date BETWEEN
      CURRENT_DATE - INTERVAL '150 days'
      AND CURRENT_DATE - INTERVAL '110 days'
  AND m.deleted_at IS NULL
  -- 교배 후 폐사한 모돈 제외
  AND NOT EXISTS (
      SELECT 1 FROM removals r
      WHERE r.sow_id = m.sow_id
        AND r.removal_date BETWEEN m.mating_date AND m.mating_date + INTERVAL '115 days'
        AND r.removal_type = 'DEAD'
  );
```

### 엣지케이스
| 케이스 | 처리 |
|--------|------|
| 유산(abortion) | 분만 실패로 카운트 (분모에만 포함) |
| 교배 후 폐사 | 분모에서 제외 |
| 복수 교배 (같은 발정 2~3회) | 첫 번째 교배만 카운트 (mating_number=1) |
| 분만 기록 지연 입력 | 150일 윈도우로 충분한 여유 |

### 벤치마크
| 지역 | 평균 | 우수 |
|------|------|------|
| KR | 80~85% | 88%+ |
| US | 78.3% | 90.2% |
| EU(DK) | 85~90% | 92%+ |

---

## 5. FCR (Feed Conversion Ratio)

### 정의
체중 1kg 증가에 소비된 사료량 (kg)

### 공식
```
FCR = SUM(사료 소비량 kg) / SUM(체중 증가량 kg)

그룹 기반:
FCR = SUM(feed_records.quantity_kg)
    / ((avg_exit_weight - avg_entry_weight) × surviving_head_count)
```

### SQL 구현
```sql
SELECT
    g.id AS group_id,
    g.group_code,
    SUM(fr.quantity_kg) AS total_feed_kg,
    (MAX(gr.avg_weight_kg) - g.entry_avg_weight_kg) * g.current_count AS total_gain_kg,
    ROUND(
        SUM(fr.quantity_kg)
        / NULLIF((MAX(gr.avg_weight_kg) - g.entry_avg_weight_kg) * g.current_count, 0)
    , 2) AS fcr
FROM animal_groups g
JOIN feed_records fr ON fr.group_id = g.id AND fr.deleted_at IS NULL
JOIN grow_records gr ON gr.group_id = g.id
WHERE g.farm_id = :farm_id
  AND g.status = 'CLOSED'  -- 출하 완료된 그룹만
GROUP BY g.id, g.group_code, g.entry_avg_weight_kg, g.current_count;
```

### 엣지케이스
| 케이스 | 처리 |
|--------|------|
| 기간 중 폐사 | 폐사 전까지 소비 사료 포함, 체중 증가에서 폐사두 제외 |
| 사료 기록 누락 | data_quality 경고, 해당 그룹 FCR = NULL |
| 체중 측정 누락 | 추정 ADG 기반 보간 (옵션) |

### 벤치마크
| 지역 | 평균 | 우수 (Top10%) |
|------|------|--------------|
| DK | 2.38 | 2.23 |
| US | ~3.0 | 2.5~2.7 |
| KR | 3.26 | 2.6 |
| BR | 2.5 | 2.3 |

---

## 6. Pre-weaning Mortality Rate (포유 중 폐사율)

### 공식
```
포유폐사율(%) = (born_alive - weaned_count) / born_alive × 100
```

### SQL
```sql
SELECT
    ROUND(
        AVG(
            (f.born_alive - COALESCE(w.weaned_count, 0))::DECIMAL
            / NULLIF(f.born_alive, 0) * 100
        )
    , 1) AS pre_weaning_mortality_pct
FROM farrowings f
LEFT JOIN weanings w ON w.farrowing_id = f.id AND w.deleted_at IS NULL
WHERE f.farm_id = :farm_id
  AND f.farrowing_date >= CURRENT_DATE - INTERVAL '365 days'
  AND f.born_alive > 0
  AND f.deleted_at IS NULL;
```

### 벤치마크
| 지역 | 평균 | 우수 |
|------|------|------|
| US | 15.8% | <9% |
| DK | 14~15% | <12% |
| KR | ~15% | <12% |

---

## 7. Sow Mortality Rate (모돈 폐사율)

### 공식
```
모돈폐사율(%) = (기간 내 폐사 두수 / 평균 모돈 재고) × 100
```

### SQL
```sql
SELECT
    COUNT(r.id) FILTER (WHERE r.removal_type = 'DEAD') AS deaths,
    AVG(active_count) AS avg_inventory,
    ROUND(
        COUNT(r.id) FILTER (WHERE r.removal_type = 'DEAD')::DECIMAL
        / NULLIF(AVG(active_count), 0) * 100
    , 1) AS sow_mortality_pct
FROM removals r
CROSS JOIN LATERAL (
    SELECT COUNT(*) AS active_count FROM sows s
    WHERE s.farm_id = :farm_id
      AND s.status NOT IN ('CULLED', 'DEAD')
      AND s.deleted_at IS NULL
) inv
WHERE r.farm_id = :farm_id
  AND r.removal_date >= CURRENT_DATE - INTERVAL '365 days';
```

### 주의
- US 평균 14.5% (2014 대비 80% 상승 — 심각)
- POP(골반장기탈출)가 미국 모돈 폐사의 21%
- `removals.pop_flag = TRUE` 별도 추적

---

## 8. ROI Dashboard (금액 환산 — Blue Ocean)

### FCR 절감 금액
```
fcr_savings = (current_fcr - target_fcr)
            × avg_daily_feed_intake_kg
            × days_to_market
            × feed_price_per_kg
            × head_count

예시 (한국):
  (3.26 - 3.16) × 2.3kg × 170일 × 450원 × 1두
  = 0.1 × 2.3 × 170 × 450 = 17,595원/두
  ≈ 두당 약 3,300원/kg 절감 (간편 표현)
```

### PSY 추가 수익
```
psy_revenue = (current_psy - benchmark_psy)
            × avg_piglet_value
            × active_sow_count

예시 (한국, 1000두 농장):
  (23 - 21.9) × 50,000원 × 1,000두
  = 1.1 × 50,000 × 1,000 = 55,000,000원/년
```

### API 응답 포맷
```json
{
  "roi_insights": [
    {
      "metric": "FCR",
      "current": 3.26,
      "target": 3.16,
      "improvement": 0.1,
      "savings_per_head": 17595,
      "savings_total": 175950000,
      "currency": "KRW",
      "message_ko": "FCR 0.1 개선 시 두당 17,595원, 연 1.76억원 절감",
      "message_en": "FCR 0.1 improvement saves ₩17,595/head, ₩176M/year"
    }
  ]
}
```

---

## 9. KPI 스냅샷 저장 정책

### 자동 집계 주기
| 주기 | 대상 KPI | 트리거 |
|------|---------|--------|
| 일별 | alert용 이상 탐지 (폐사율 급등 등) | 크론잡 03:00 UTC |
| 월별 | PSY/NPD/FCR/분만율 전체 | 월 1일 00:00 UTC |
| 분기별 | 벤치마크 비교 리포트 | 분기 첫날 |

### 월마감 연동
```
1. 월마감 전: kpi_snapshots INSERT (period_type = 'MONTHLY')
2. 월마감 실행: period_locks.locked = TRUE
3. 이후 해당 기간 kpi_snapshots 수정 불가 (HTTP 423)
4. 잠금 해제 시: audit_log에 사유 기록 필수
```

---

*이 문서의 공식과 SQL은 MVP 개발의 기준이다. 변경 시 이 문서를 먼저 업데이트할 것.*
