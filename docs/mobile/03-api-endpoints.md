# API 엔드포인트 레퍼런스

Base URL: `https://api.pigos.io/api/v1` (개발: `http://10.0.2.2:8000/api/v1`)

모든 요청 (인증 필요): `Authorization: Bearer {accessToken}`  
Public 엔드포인트: 별도 표기

---

## 인증 (Auth)

| Method | Path | 설명 | Auth |
|--------|------|------|------|
| POST | `/auth/login` | 로그인 | ❌ |
| POST | `/auth/refresh` | 토큰 갱신 | ❌ |
| POST | `/auth/logout` | 로그아웃 | ✅ |
| GET | `/auth/me` | 내 정보 | ✅ |

---

## 온보딩 (Onboarding)

| Method | Path | 설명 |
|--------|------|------|
| POST | `/onboarding/complete` | 조직+농장+계정 일괄 생성 |
| POST | `/onboarding/farm` | 농장 추가 생성 |
| POST | `/onboarding/farm/{farm_id}/config` | 농장 설정 저장 |
| GET | `/onboarding/farm/{farm_id}/status` | 온보딩 완료 여부 확인 |

---

## 농장 (Farms)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/farms` | 내 농장 목록 |
| GET | `/farms/{farm_id}` | 농장 상세 |
| PATCH | `/farms/{farm_id}` | 농장 정보 수정 |

---

## 모돈 (Sows)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/farms/{farm_id}/sows` | 모돈 목록 (페이지네이션) |
| POST | `/farms/{farm_id}/sows` | 모돈 등록 |
| GET | `/farms/{farm_id}/sows/{sow_id}` | 모돈 상세 |
| PATCH | `/farms/{farm_id}/sows/{sow_id}` | 모돈 정보 수정 |
| POST | `/farms/{farm_id}/sows/{sow_id}/cull` | 도폐사 처리 |
| DELETE | `/farms/{farm_id}/sows/{sow_id}` | 모돈 삭제 |

### 모돈 목록 Query Params
```
status: ACTIVE | GESTATING | LACTATING | WEANED | DRY | CULLED | DEAD
page: int (기본 1)
per_page: int (기본 50, 최대 100)
```

---

## 이벤트 (Events)

모든 경로: `/farms/{farm_id}/events/`

| Method | Path | 설명 |
|--------|------|------|
| GET | `/events/matings` | 교배 이력 |
| POST | `/events/matings` | 교배 기록 |
| GET | `/events/farrowings` | 분만 이력 |
| POST | `/events/farrowings` | 분만 기록 |
| GET | `/events/weanings` | 이유 이력 |
| POST | `/events/weanings` | 이유 기록 |
| POST | `/events/reproductive` | 임신사고 기록 (반발정/유산/공태 등) |

### 교배 기록 Request Body
```json
{
  "sow_id": "uuid",
  "mating_date": "2026-06-05",
  "mating_type": "AI",          // AI | NATURAL
  "semen_batch": "SB-001",      // optional
  "notes": ""                   // optional
}
```

### 분만 기록 Request Body
```json
{
  "sow_id": "uuid",
  "farrowing_date": "2026-06-05",
  "born_alive": 12,
  "stillborn": 1,
  "mummified": 0,
  "notes": ""
}
```

### 이유 기록 Request Body
```json
{
  "sow_id": "uuid",
  "weaning_date": "2026-06-05",
  "weaned_count": 11,
  "avg_weaning_weight_kg": 7.5,  // optional
  "notes": ""
}
```

### 임신사고 Request Body
```json
{
  "sow_id": "uuid",
  "event_type": "RETURN_TO_ESTRUS",  // RETURN_TO_ESTRUS | ABORTION | EMPTY | INFERTILE | HEAT_DETECTED
  "event_date": "2026-06-05",
  "notes": ""
}
```

---

## KPI

| Method | Path | 설명 |
|--------|------|------|
| GET | `/farms/{farm_id}/kpi/dashboard` | 대시보드 KPI (PSY, NPD, 분만율, 알림) |
| GET | `/farms/{farm_id}/kpi/psy` | PSY 상세 |
| GET | `/farms/{farm_id}/kpi/npd` | NPD 상세 |

### KPI Dashboard Response
```json
{
  "psy": 24.3,
  "npd": 32.1,
  "farrowing_rate": 0.912,
  "gestating": 218,
  "lactating": 85,
  "weaned": 42,
  "active_sows": 380,
  "as_of": "2026-06-05",
  "alerts": [
    {
      "rule_id": "PSY_LOW",
      "kpi": "PSY",
      "severity": "WARNING",
      "message": "PSY가 목표치(28.0) 미달입니다",
      "current_value": 24.3,
      "target_value": 28.0
    }
  ]
}
```

---

## Q&A (Chat)

| Method | Path | 설명 |
|--------|------|------|
| POST | `/farms/{farm_id}/chat/query` | Rule Engine 기반 Q&A |

### Request
```json
{
  "question": "PSY가 왜 낮아요?",
  "locale": "ko"              // en | ko | zh | es | vi
}
```

### Response
```json
{
  "intent": "explain_psy",
  "severity": "WARNING",
  "answer": "현재 PSY 24.3은 목표(28.0) 대비 낮습니다...",
  "findings": [
    {
      "rule_id": "PSY_LOW",
      "kpi": "PSY",
      "severity": "WARNING",
      "current_value": 24.3,
      "target_value": 28.0,
      "causes": ["npd_high", "farrowing_rate_low"],
      "recommended_actions": ["check_breeding_timing", "review_nutrition"]
    }
  ],
  "farm_id": "uuid",
  "as_of": "2026-06-05",
  "renderer": "template"
}
```

---

## 비육돈 (Finishers)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/farms/{farm_id}/finishers` | 비육돈 그룹 목록 |
| POST | `/farms/{farm_id}/finishers` | 그룹 입식 |
| POST | `/farms/{farm_id}/finishers/{group_id}/ship` | 출하 처리 |
| DELETE | `/farms/{farm_id}/finishers/{group_id}` | 그룹 삭제 |

---

## 자돈 (Piglets)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/farms/{farm_id}/piglets` | 자돈 그룹 목록 |
| POST | `/farms/{farm_id}/piglets` | 그룹 시작 |
| POST | `/farms/{farm_id}/piglets/{group_id}/deaths` | 폐사 기록 |
| POST | `/farms/{farm_id}/piglets/{group_id}/transfer` | 전출/판매 |
| POST | `/farms/{farm_id}/piglets/transfers` | 개별 양자 이동 |
| GET | `/farms/{farm_id}/piglets/transfers` | 양자 이동 이력 |

---

## 오프라인 동기화 (Sync)

| Method | Path | 설명 |
|--------|------|------|
| POST | `/farms/{farm_id}/sync` | 로컬 변경사항 업로드 + 서버 변경사항 다운로드 |

→ 상세: [05-offline-sync.md](05-offline-sync.md)

---

## Public (인증 불필요)

| Method | Path | 설명 |
|--------|------|------|
| POST | `/pilot-signups` | 파일럿 신청 (랜딩 페이지 폼) |

---

## 에러 코드

| HTTP | detail | 의미 |
|------|--------|------|
| 400 | `missing_fields` | 필수 필드 누락 |
| 401 | `not_authenticated` | 토큰 없음/만료 |
| 403 | `forbidden` | 권한 없음 |
| 404 | `not_found` | 리소스 없음 |
| 409 | `duplicate_email` | 이메일 중복 |
| 422 | (Pydantic) | 입력값 형식 오류 |
| 423 | `period_locked` | 기간 잠금 |
| 500 | `db_error` | 서버 오류 |
