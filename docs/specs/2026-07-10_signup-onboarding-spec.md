# 회원가입 / 온보딩 기능명세 (Web ↔ Mobile 공용)

> 목적: 웹과 모바일(React Native)이 **동일한 가입 플로우·필드·검증·API**를 쓰도록 단일 명세화.
> 핵심 요구: **국가 선택 + 언어셋에 따라 입력항목·기본값이 달라진다.**
> 작성 2026-07-10. 기준 구현: `src/app/onboarding/page.tsx`, `api/app/schemas/auth.py::OnboardingCompleteRequest`, `POST /api/v1/onboarding/complete`.
>
> 표기: **[B]=현재 구현된 baseline** · **[P]=국가별 파리티 확장**. 모바일은 [B]를 먼저 100% 일치시키고, [P]는 웹과 동시 반영.
>
> **구현 상태 (2026-07-10 갱신)**: 단일 소스 국가설정(`api/app/core/countries.py`) + 공개 엔드포인트
> `GET /api/v1/config/countries` + 온보딩 **통화·단위·타임존 국가 자동파생** + **RU(러시아) 국가 추가** = **구현·배포대기**.
> 잔여 [P]: phone·business_id 입력필드, 농장유형별 필드가변(NURSERY/FINISHER).

---

## 1. 플로우 개요

3-step 위저드 → 마지막에 **원샷 API 1회** 호출(org+user+farm 동시 생성, 즉시 토큰 발급).

```
[Step 0] 농장 정보  →  [Step 1] 계정  →  [Step 2] 확인  →  POST /onboarding/complete  →  토큰 → 홈(/)
```

- 서버 라운드트립은 **제출 1회뿐** (스텝 이동은 클라 로컬 상태). 모바일도 동일 — 오프라인서 스텝 작성, 제출만 온라인.
- pre-auth 화면: 언어는 `NEXT_LOCALE` 쿠키(웹) / 디바이스 로케일(모바일)에서 결정. **한국어(ko)는 관리자 전용 → 공개 가입 화면엔 노출 안 함.**
- 대체 확장 플로우(고급): `POST /auth/register` → `/onboarding/farm` → `/farm/{id}/config`. **모바일 MVP는 원샷(`/complete`)만 구현.**

---

## 2. 국가 설정 매트릭스 (★ 이 명세의 핵심)

국가를 선택하면 아래가 **자동 결정/프리필**된다. 사용자는 이후 개별 변경 가능.

| 국가 | ISO | 기본 언어 | 타임존 | 통화 | 단위계 | 국제전화 | 사업자ID 라벨/형식 [P] |
|---|---|---|---|---|---|---|---|
| 한국 | KR | ko¹ | Asia/Seoul | KRW | metric | +82 | 사업자등록번호 `###-##-#####` |
| 미국 | US | en | America/Chicago | USD | **imperial²** | +1 | EIN / Farm ID (선택) |
| 중국 | CN | zh | Asia/Shanghai | CNY | metric | +86 | 统一社会信用代码 (18) |
| 베트남 | VN | vi | Asia/Ho_Chi_Minh | VND | metric | +84 | Mã số thuế (선택) |
| 태국 | TH | th | Asia/Bangkok | THB | metric | +66 | เลขประจำตัวผู้เสียภาษี (선택) |
| 필리핀 | PH | en | Asia/Manila | PHP | metric | +63 | TIN (선택) |
| 브라질 | BR | pt | America/Sao_Paulo | BRL | metric | +55 | CNPJ `##.###.###/####-##` |
| 멕시코 | MX | es | America/Mexico_City | MXN | metric | +52 | RFC (선택) |
| 칠레 | CL | es | America/Santiago | CLP | metric | +56 | RUT `##.###.###-#` |
| 러시아³ | RU | ru | Europe/Moscow | RUB | metric | +7 | ИНН (선택) |

¹ **KR 기본 ko는 관리자 컨텍스트 한정.** 공개 가입에서 KR 선택 시 언어는 사용자가 명시 선택한 로케일 유지(ko 자동선택 안 함 — 해외 출시 정책).
² **미국만 imperial** (체중 lb, 온도 °F). 나머지 metric(kg, °C). 이 값이 `farm.unit_system`으로 저장돼 앱 전체 입력/표시 단위를 결정.
³ **RU는 언어(ru)만 이미 구현됨. 가입 국가 목록(RU) 포함 여부는 §10 미결정.** 언어 ≠ 국가: 어느 국가 사용자든 러시아어 UI 선택 가능.

> 구현: 이 매트릭스를 웹/모바일 공용 상수(`COUNTRY_CONFIG`)로 둔다. 웹은 `src/app/onboarding/page.tsx`의 `COUNTRIES`(현재 value/label/tz만) → 이 매트릭스로 확장. 모바일은 동일 JSON을 공유 패키지/자산으로.

---

## 3. 필드 명세

### Step 0 — 농장 정보

| 필드 | 상태 | 타입/위젯 | 필수 | 검증 | i18n | 모바일 위젯 |
|---|---|---|---|---|---|---|
| 조직/회사명 `org_name` | [B] | text | ✔ | 1–200자 | `org` | TextInput |
| 농장명 `farm_name` | [B] | text | ✔ | 1–200자 | `farm` | TextInput |
| 국가 `country` | [B] | select | ✔ | ISO alpha-2, 목록 내 | `country` | **네이티브 Picker** (국기+국가명) |
| 농장 유형 `farm_type` | [B] | select | (기본 F2F) | `SOW_FARM\|FARROW_TO_FINISH\|NURSERY\|FINISHER` | `ftype` | 세그먼트/Picker |
| 모돈수 `sow_count` | [B] | number | 선택 | ≥1 정수 (기본 100) | `sows` | 숫자패드 |
| 통화 `currency` | [P] | select | 국가서 프리필 | ISO 4217 | `currency` | Picker(기본=국가값) |
| 단위계 `unit_system` | [P] | toggle | 국가서 프리필 | `metric\|imperial` | `units` | 세그먼트 |
| 지역/주 `region` | [P] | text/select | 선택 | 자유입력(국가별 주 목록 optional) | `region` | TextInput |

> **국가 유형별 노출 규칙 [P]**: `NURSERY`/`FINISHER`(자돈·비육 전용) 선택 시 `sow_count` 라벨을 "입식두수"로 바꾸고, 번식 기본값(임신/포유기간) 설정 스텝은 스킵.

### Step 1 — 계정

| 필드 | 상태 | 타입 | 필수 | 검증 | i18n |
|---|---|---|---|---|---|
| 이름 `name` | [B] | text | ✔ | 1–100자 | `name` |
| 아이디 `username` | [B] | text | ✔ | `^[a-zA-Z0-9_.-]{3,50}$` **+ 예약어 차단**(§5) | `username` |
| 이메일 `email` | [B] | email | ✔ | RFC email, unique(서버) | `email` |
| 비밀번호 `password` | [B] | password | ✔ | 최소 8자 | `pw` |
| 비밀번호 확인 `confirmPw` | [B] | password | ✔ | `password`와 일치 | `cpw`/`mismatch` |
| 휴대폰 `phone` | [P] | tel | 선택 | 국가 dial code 프리필 + E.164 | `phone` |
| 사업자ID `business_id` | [P] | text | 선택 | **국가별 형식**(§2 매트릭스) | 국가별 동적 라벨 |

> `username` 실시간 검증: 정규식 + 예약어(`admin/pigos/wiselake/...`) 즉시 피드백. 모바일도 동일 정규식·예약어 세트 공유.
> `confirmPw`는 API에 전송 안 함(클라 전용). 불일치 시 인라인 에러.

### Step 2 — 확인

- Step 0/1 입력 요약 카드(조직·농장·국가·유형·모돈수·이름·이메일) 표시.
- "무료 시작, 카드 불필요" 안내.
- 제출 버튼 → `POST /onboarding/complete`.

---

## 4. 국가/언어 변경 시 반응 규칙

| 트리거 | 동작 |
|---|---|
| **국가 변경** | `timezone`·`currency`·`unit_system`·`phone` dial code·`business_id` 라벨/형식을 매트릭스 값으로 **자동 갱신**(사용자가 이미 수동변경한 필드는 유지). [B]: 현재 timezone만 자동설정됨 → [P] 나머지 확장 |
| **언어(로케일) 변경** | UI 텍스트만 교체. 입력값 불변. 언어는 국가와 **독립**(예: 칠레 농장이 영어 UI 선택 가능) |
| **농장유형=NURSERY/FINISHER** | `sow_count` 라벨→"입식두수", 번식 파라미터 스텝 스킵 [P] |

> 핵심: **언어와 국가는 분리**한다. 국가=데이터/단위/통화/타임존, 언어=화면 텍스트. "언어셋 따라 입력항목이 다르다"는 실제로는 **국가 따라 입력항목이 다르다**로 구현하고, 언어는 라벨 번역만 담당.

---

## 5. 검증 · 에러

- **예약 아이디**(서버 `validate_username_not_reserved` + 클라 `RESERVED_UN`): `admin/administrator/root/pigos/pigplan/wiselake/superadmin/support/billing/api/...` 및 `admin*` 접두, leetspeak 변형 차단 → 422.
- **이메일 중복**: 서버 unique 위반 → 4xx + `detail` 메시지 그대로 표시.
- **비밀번호**: 최소 8자(서버 강제). [P] 강도 미터(선택).
- 서버 에러: `err.response.data.detail` 문자열이면 그대로 노출, 아니면 일반 메시지.
- i18n: 검증 메시지도 로케일별(§ `validation` 네임스페이스). 모바일 동일 키 사용.

---

## 6. API 계약

### 요청 `POST /api/v1/onboarding/complete`
```jsonc
{
  "org_name":  "string(1..200)",       // [B]
  "farm_name": "string(1..200)",       // [B]
  "country":   "KR",                   // [B] ISO alpha-2
  "farm_type": "FARROW_TO_FINISH",     // [B] 기본값
  "sow_count": 100,                    // [B] optional ≥1
  "name":      "string(1..100)",       // [B]
  "username":  "string ^[a-zA-Z0-9_.-]{3,50}$", // [B] 예약어 차단
  "email":     "user@example.com",     // [B]
  "password":  "string ≥8",            // [B]
  "timezone":  "Asia/Seoul",           // [B] 국가서 프리필(default UTC)
  "language":  "ko",                   // [B] 감지 로케일 전송(default en)
  "currency":     "KRW",               // [P] 국가서 프리필
  "unit_system":  "metric",            // [P] 국가서 프리필
  "phone":        "+8210...",          // [P] optional
  "business_id":  "###-##-#####"       // [P] optional
}
```

### 응답 `201`
```jsonc
{ "org_id","farm_id","user_id","access_token","refresh_token" }
```
> 성공 시: 토큰 저장 + `pigos_session` 쿠키(웹)/시큐어스토어(모바일), `identify/track("signup",{country})` 애널리틱스, 홈(`/`) 이동.
> [P] 추가 필드(currency/unit_system/phone/business_id)는 `OnboardingCompleteRequest` 스키마 + `complete_onboarding` 서비스 확장 필요(farm에 저장). 미도입 시 country에서 서버가 파생.

---

## 7. 모바일 구현 노트 (React Native)

- **국가/농장유형/통화**: 네이티브 Picker(iOS Wheel / Android Dropdown). 국가는 국기 이모지 + 현지어 국가명.
- **로케일 감지**: `expo-localization` 등 디바이스 로케일 → 공개 로케일 중 매칭, ko면 en 폴백. 이후 앱 언어토글로 override(설정 화면).
- **비밀번호/아이디**: 웹과 **동일 정규식·예약어 상수 공유**(중복정의 금지 — 공용 패키지).
- **오프라인**: 스텝 작성은 오프라인 가능, 제출만 네트워크. 실패 시 폼 상태 보존 재시도.
- **딥링크**: 이메일 인증/비번재설정(`/verify-email`, `/forgot-password?token=`)은 모바일 딥링크 매핑.
- **보안**: 토큰은 Keychain/Keystore(SecureStore), 평문 저장 금지.
- **단위 표시**: `unit_system=imperial`(US)면 앱 전역 체중 lb·온도 °F 렌더 — 온보딩서 확정된 값이 전 화면 기준.

---

## 8. i18n 키

- 온보딩 텍스트는 현재 `src/app/onboarding/page.tsx`의 인라인 `OT` 사전(en/zh/es/vi/th/pt/ru + ko는 admin) 사용. 모바일도 동일 키셋 공유.
- [P] 신규 필드 라벨(`currency/units/region/phone/business_id`)·국가별 사업자ID 라벨은 8개 로케일 동시 추가.

---

## 9. 화면 흐름도

```
 시작(/onboarding)
   │  로케일 감지(쿠키/디바이스) → 공개 로케일, ko→en
   ▼
 Step0 농장정보 ──(국가 선택 시 tz/통화/단위/전화코드 자동)──►
   │  canProceed: org_name·farm_name·country
   ▼
 Step1 계정
   │  canProceed: name·username(정규식+예약어)·email·pw≥8·pw==confirm
   ▼
 Step2 확인 ──[제출]──► POST /onboarding/complete
   │  201: 토큰저장·세션쿠키·analytics·홈이동
   └  4xx: detail 인라인 표시(중복이메일/예약아이디 등)
```

---

## 10. 미결정 / 제안

1. **RU를 가입 국가 목록에 추가할지** — ru 언어는 구현됨. 러시아 농장 가입 실수요 있으면 §2에 RU 활성화(tz=Europe/Moscow, currency=RUB). 언어만 필요하면 국가 목록 제외 유지.
2. **[P] 필드 실제 도입 범위** — currency/unit_system은 앱 전반(원가리포트·체중입력)에 영향 크므로 우선 권장. phone/business_id는 B2B 계약·정산 도입 시점에.
3. **`unit_system` 백엔드 컬럼** — `farms`에 없으면 마이그레이션 추가 필요(현재 currency는 있음, default USD).
4. **국가별 사업자ID 검증 강도** — MVP는 자유입력(형식 힌트만), 정산 도입 시 정규식 강제.
