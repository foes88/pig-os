# PigOS 모바일 ↔ 백엔드 연동 계약서 (Single Source of Truth)

> 웹/백엔드 세션과 모바일(iOS/Android) 세션이 **이 문서 하나를 보고** 개발을 맞춘다.
> 변경 시 이 문서를 먼저 갱신하고 양측에 공지. 최종 갱신: 2026-06-16.
> API 라우트는 `GET http://<host>:8000/docs` (OpenAPI)와 항상 일치해야 한다.
>
> ⛔ **이 문서가 유일한 기준.** 모바일 레포의 옛 문서(`03-api-endpoints.md`,
> `MOBILE_API_CHANGES_2026-06-09.md` 등)는 stale(모돈 상태값 오류·boars "미구현" 오인 등) →
> **폐기**하고 이 계약서로 대체한다. 라이브 백엔드 라우트에서 직접 생성됨(커밋 66528f7+).

---

## 1. API Base URL (환경별)

| 환경 | Base URL | 비고 |
|------|----------|------|
| 운영(prod) | `https://api.pigos.io` | 포트 없음, HTTPS |
| Android 에뮬레이터 | `http://10.0.2.2:8000` | 에뮬에서 본 PC localhost |
| iOS 시뮬레이터 | `http://localhost:8000` | 호스트 네트워크 공유 |
| 실기기(같은 와이파이) | `http://<PC-LAN-IP>:8000` | 예: 192.168.x.x, PC IP 바뀌면 교체 |

- dev API 포트 **8000 고정**. 웹 프론트는 3000.
- 환경 분리: Android `BuildConfig.API_BASE_URL`(debug/release), iOS `Debug/Release.xcconfig`.
- dev는 평문 HTTP → Android `usesCleartextTraffic`(debug만), iOS ATS `NSAllowsLocalNetworking`(debug만).
- 모든 경로 prefix: `/api/v1`.

---

## 2. 인증 (Bearer 토큰, 쿠키 아님)

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/api/v1/auth/login` | `{email, password}` → `{access_token, refresh_token, user_id, name, email, role, farm_ids}` |
| POST | `/api/v1/auth/refresh` | `{refresh_token}` → `{access_token}` |
| POST | `/api/v1/auth/logout` | 로그아웃 |
| GET | `/api/v1/auth/me` | 현재 유저 프로필 |
| POST | `/api/v1/auth/register` | 가입(개별) |

- 모든 보호 API는 헤더 `Authorization: Bearer <access_token>`.
- access 만료 시 401 → refresh로 재발급 → 원요청 재시도 (모바일 인터셉터 구현 필요).
- 테스트 계정: `test001@pigos.io` / `123123` (FARM_OWNER).
- 온보딩(신규 농장): `POST /api/v1/onboarding/complete` 등 `/onboarding/*`.

---

## 3. 핵심 도메인 API (모바일 화면별)

### 농장 컨텍스트 / 설정
- `GET /farms` · `GET /farms/{farm_id}` · `PATCH /farms/{farm_id}`
- `GET /farms/{farm_id}/config` → 단위/통화 (`weight_unit, currency_code, currency_symbol, ...`, **country 기준 자동 분기**)
- `GET|PATCH /farms/{farm_id}/config/repro` → 임신/포유/WSI 기준일

### 모돈 / 웅돈 / 자돈 / 비육
- 모돈: `GET|POST /farms/{farm_id}/sows`, `GET|PATCH|DELETE /sows/{sow_id}`, `POST /sows/{sow_id}/cull`, `GET /sows/removals`
  - 목록 쿼리: `status, building_id, parity_min, parity_max, search(ear_tag 부분일치), page, per_page`
- 웅돈: `GET|POST /farms/{farm_id}/boars`, `GET|PATCH /boars/{boar_id}`
- 자돈: `GET|POST /farms/{farm_id}/piglets`, `/piglets/{group_id}/deaths`, `/piglets/{group_id}/transfer`, `/piglets/transfers`
- 비육: `GET|POST /farms/{farm_id}/finishers`, `PATCH|DELETE /finishers/{group_id}`, `POST /finishers/{group_id}/ship`

### 번식 이벤트 (수정/삭제 = 상태 롤백 + 월마감 423 포함)
- 교배: `GET|POST /events/matings`, `PATCH|DELETE /events/matings/{id}`
- 분만: `GET|POST /events/farrowings`, `PATCH|DELETE /events/farrowings/{id}`
- 이유: `GET|POST /events/weanings`, `PATCH|DELETE /events/weanings/{id}`
- 기타: `POST /events/reproductive`(임신사고/RTS 등), `GET|POST /events/piglet_events`(포유자돈 폐사)
- 이벤트 정의: `GET /events/definitions`

### KPI / 보고서 / 분석
- `GET /farms/{farm_id}/kpi/dashboard` (PSY/NPD/FR + 모돈현황 + alerts + **country별 benchmarks**)
- `GET /kpi/psy` · `/kpi/npd` · `/kpi/trend?kpi=&months=`
- `GET /reports/reproduction?start&end&period` · `/reports/grow-finish` · `/reports/sows/{sow_id}/history`
- `GET /farms/{farm_id}/analytics/prrs-by-genetics`

### 할 일 / 알림
- 오늘 할 일: `GET /farms/{farm_id}/tasks?status=&assigned_to=`, `POST /tasks/generate`, `PATCH /tasks/{id}`(DONE/DISMISS/assign)
- 관리대상: `GET /farms/{farm_id}/alerts/overdue` · `/alerts/cull-candidates`
- 인앱 알림: `GET /api/v1/notifications?unread_only=&limit=&offset=` (유저 스코프, `unread_count` 포함),
  `PATCH /notifications/{id}/read`, `POST /notifications/read-all`, 생성배치 `POST /farms/{farm_id}/notifications/generate`

### 푸시 디바이스 (G2 — 신설)
- `POST /api/v1/devices` `{platform: ANDROID|IOS|WEB, token, app_version?}` → 등록(토큰 기준 upsert)
- `GET /api/v1/devices` → 내 단말 목록
- `DELETE /api/v1/devices/{token}` → 로그아웃/토큰만료 시 해제
- 모바일 흐름: 로그인 직후 FCM/APNS 토큰 등록 → 토큰 갱신 시 재등록 → 로그아웃 시 삭제.

### Q&A
- `POST /farms/{farm_id}/chat/query` (Rule-grounded, addon 활성 농장은 LLM 응답)

---

## 4. 오프라인 동기화 (Offline Sync)

- 엔드포인트: `POST /api/v1/farms/{farm_id}/sync`
- 스펙 문서: `docs/specs/2026-05-19_offline-sync-spec.md` (Last-Write-Wins)
- **Push(클라→서버)** 커버 엔티티: `matings, farrowings, weanings, sows, piglet_events`
- **Pull(서버→클라)** 커버 엔티티: `sows, matings, farrowings, weanings, piglet_events, removals`
- 충돌: 자동 LWW 병합, 해소 불가(DUPLICATE_EVENT/CYCLE_CONFLICT)만 `sync_conflict_queue` 적재.
- ⚠️ 모바일 로컬 스키마(Room/CoreData)는 위 엔티티 + 필드와 1:1 유지. 필드 추가 시 이 문서 갱신.

---

## 5. 공유 상수 / Enum (양측 동일하게)

- **모돈 상태(SowStatus v2)**: `GILT, OPEN, PREGNANT, LACTATING, ACCIDENT`(활성) / `CULLED, DEAD, SOLD, TRANSFER`(종료)
  - 상태 머신 출처: `docs/SCREEN_MENU_SPEC.md`. PATCH로는 활성값만, 종료는 `/cull` 전용.
- **입식유형(entry_type)**: `GILT, PURCHASE, TRANSFER, BORN`
- **번식 이벤트(reproductive) event_type (9종)**: `RETURN_TO_ESTRUS, ABORTION, EMPTY, INFERTILE, HEAT_DETECTED, CULLED, DEAD, TRANSFER_OUT, SOLD`
  - `detected_method`(선택): `ULTRASOUND, VISUAL, BEHAVIOR, BLOOD_TEST`
- ⚠️ `GET /sows?status=` 는 위 SowStatus 값만 허용 — 잘못된 값은 **422**(빈 목록 조용히 반환 아님). 옛 값(ACTIVE/GESTATING/DRY/WEANED) 사용 금지.
- **Task 유형**: overdue 6유형(`gilt_no_estrus, gilt_overdue_mating, pregnant_overdue_farrowing, lactating_overdue_weaning, open_overdue_mating, accident_overdue_mating`) + `cull_candidate`
- **알림 severity**: `INFO, WARNING, CRITICAL` / **alert_type**: `OVERDUE_*, CULL_CANDIDATE, KPI_*`
- **역할**: `FARM_OWNER, FARM_MANAGER, FARM_WORKER, VET, VIEWER` (org: `SUPER_ADMIN` 등)
- **단위/통화**: 하드코딩 금지 — 반드시 `GET /farms/{id}/config` 응답 사용. country는 계정별로 다름(언어≠국가).

---

## 6. 갭 현황 (2026-06-16 갱신)

| # | 갭 | 상태 | 비고 |
|---|----|------|------|
| **G1** | 푸시 전송(FCM HTTP v1) | ✅ **코드 완성** | `push_service.send_push` + 알림 잡 연동. **배포 활성화 2단계 필요**: ① `uv add google-auth` ② env `FCM_PROJECT_ID`+`FCM_CREDENTIALS_PATH`(서비스계정 JSON). 미설정 시 graceful skip. |
| **G2** | 디바이스/푸시토큰 등록 API | ✅ **완성** | `POST/GET/DELETE /api/v1/devices` + `devices` 테이블 + 테스트. |
| **G3** | 알림 producer 자동 실행 | ✅ **cron 등록됨** | `worker.py`: tasks 05:30 / notifications 06:00 (UTC). **배포 시 ARQ worker 컨테이너 상시기동 확인 필요**(인프라). |
| **G4** | sync 실단말 E2E 검증 | 🟡 **모바일 대기** | 서버측 구현·테스트 완료. 닫는조건: 실기기에서 오프라인 입력→온라인 복귀→`POST /sync` 왕복 + 충돌 1건 시나리오 통과(모바일+백엔드 합동). |
| **G5** | 이미지 업로드(사진 첨부) | ⚪ **보류(요구 확정 전)** | 닫는조건: ① 제품 요구 확정 ② S3 버킷+IAM 준비 → `POST /api/v1/uploads/presign` 신설. AWS 리소스는 사람이 생성. |
| **G6** | `/sync` 분만·자돈 영속(#8) | ✅ **수정+가드(2026-06-16)** | `_process_farrowing` kwarg(born_dead→stillborn 등)+mating_id+flush 교정(`9fc008a`). **2회 회귀 이력** — `_process_*` 직접 path만 테스트돼 `/sync` path가 무방비였음. **회귀테스트 `tests/integration/test_sync_farrowing.py`(`5511236`) 추가** → ⚠️ **`sync_service.py` 수정 시 반드시 `uv run pytest tests/integration/test_sync_farrowing.py` 확인**. 라이브 §8a 그린(farrowings/piglet_events 영속 확인). |

> **G1 활성화 메모(배포 담당)**: google-auth 설치 + 서비스계정 JSON 마운트 + env 2개. 그 전까지 푸시는 자동 skip이며
> 인앱 알림(GET /notifications)은 polling으로 정상 동작 → 기능 차단 없음.

---

## 7. 개발 체크리스트 (양 팀 공통)

**백엔드(웹 세션)**
- [x] G1 FCM HTTP v1 전송 구현 (env-gated, graceful skip)
- [x] G2 `POST /devices` 토큰 등록 엔드포인트
- [ ] 배포 시 G1 활성화(google-auth + FCM env) + G3 worker 컨테이너 기동
- [x] OpenAPI 스펙 자동생성기(`api/scripts/gen_openapi.py`) — 라우트 변경 후 재생성하면 항상 일치
- [ ] 신규/변경 엔드포인트는 이 문서 §3 갱신 + `gen_openapi.py` 재생성 + 모바일 공지

**모바일(iOS/Android 세션)**
- [ ] §1 Base URL 환경분리 + dev 평문 예외(디버그만)
- [ ] §2 auth 인터셉터(401→refresh→재시도)
- [ ] §3 로그인 직후 `POST /devices`로 FCM/APNS 토큰 등록, 로그아웃 시 `DELETE /devices/{token}`
- [ ] §4 로컬 스키마를 sync 엔티티와 1:1 정렬 → G4 실단말 E2E
- [ ] §5 Enum/상수 하드코딩 금지, config 응답 사용

**공통**
- [ ] 계약 변경 = 이 문서 먼저 수정 → 커밋 → 양측 공지
- [ ] 릴리스 전 §6 갭 전부 closed 또는 "다음 버전" 명시 합의

---

## 8. 검증 분리 — "계약 1벌 + 플랫폼별 통합 2벌"

API/계약은 플랫폼 무관 → **공유 검증 1벌**. 단말 글루는 **iOS/Android 각각** 검증.

### 8a. 공유 계약 검증 (플랫폼 무관, 한 번만 — 라이브 API 대상)
1. auth: login → `Authorization: Bearer` → 401 시 refresh → 재시도
2. 농장/설정: `GET /farms/{id}/config` 단위·통화 수신, country별 KPI 분기
3. 모돈/이벤트: 모돈 목록·검색, 교배/분만/이유 POST→PATCH→DELETE(상태 롤백)
4. 할 일/알림: `GET /tasks`, `GET /notifications`(+unread_count), read/read-all
5. sync: `POST /sync` push/pull 왕복, 6개 엔티티 필드 매핑
6. devices: `POST /devices` 등록 → `DELETE /devices/{token}` 해제

> 이 시나리오는 응답 JSON·상태코드 기준이라 iOS/Android 결과가 같아야 한다. 다르면 클라 글루 버그.

### 8b. 플랫폼별 글루 검증 (iOS / Android 각각)
| 검증 항목 | Android | iOS |
|---|---|---|
| dev 연결 | 에뮬 `10.0.2.2:8000` 도달 | 시뮬 `localhost:8000` 도달 |
| 평문 허용(디버그) | `usesCleartextTraffic` 적용 | ATS `NSAllowsLocalNetworking` |
| 토큰 갱신 인터셉터 | OkHttp Authenticator | URLSession retry / Alamofire |
| 푸시 등록 | FCM 토큰 → `POST /devices {platform:"ANDROID"}` | APNS→FCM → `{platform:"IOS"}` |
| 오프라인 저장 | Room ↔ sync 엔티티 1:1 | CoreData ↔ sync 엔티티 1:1 |
| 백그라운드 sync | WorkManager 주기/재시도 | BGTaskScheduler |
| G4 E2E | 비행기모드 입력→복귀→sync 왕복 | 동일 시나리오 |

### 결론
- **계약(8a)**: 변경 시 이 문서 기준으로 양 플랫폼이 동일 결과 확인 → 공유.
- **글루(8b)**: 네트워크 설정·푸시·로컬DB·백그라운드는 OS API가 달라 **반드시 별개 검증**.
- 릴리스 게이트: 8a 공통 통과 + 8b를 iOS·Android **각각** 통과.
