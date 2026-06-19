# 모바일 핸드오프 — iOS/Android 세션 전달 절차

> 모바일(iOS/Android) Claude Code 세션에게 "웹과 동일 기능/화면을 빠짐없이" 개발시키는 표준 절차.
> SSOT = `docs/mobile-integration-contract.md`(구조·결정·Enum·화면) + `docs/api/openapi-v1.yaml`(필드 스키마).
> 최종 갱신: 2026-06-18.

---

## 1. 계약서 2벌을 모바일 레포로 동기화 (변경 때마다)

모바일 세션은 각자 레포에서 돈다 → 백엔드 계약서를 모바일 레포 안에 복사해야 자기 레포만 보고 개발한다.
- iOS: `wiselake/pigos-ios` · Android: `wiselake/pigos-android`

```bash
# 각 모바일 레포에서 (백엔드 계약 변경 때마다 재실행)
mkdir -p docs/contract
cp /c/dev/PigOS/docs/mobile-integration-contract.md       docs/contract/
cp /c/dev/PigOS/docs/api/openapi-v1.yaml                  docs/contract/
cp /c/dev/PigOS/docs/specs/2026-05-19_offline-sync-spec.md docs/contract/
git add docs/contract && git commit -m "docs: sync backend contract (YYYY-MM-DD)"
```

> 백엔드에서 라우트/스키마가 바뀌면: `cd api && uv run python scripts/gen_openapi.py` 재생성 → 위 `cp` 재복사 → 모바일 세션에 "docs/contract 갱신됨" 한 줄 공지.

---

## 2. Android 세션 프롬프트 (pigos-android)

```
cd <pigos-android> && claude --dangerously-skip-permissions
```
```
/loop docs/contract/ 의 mobile-integration-contract.md(SSOT) + openapi-v1.yaml(필드 스키마) + offline-sync-spec.md 를 정독하고, 웹과 동일 기능/화면을 빠짐없이 구현해. 스택: Kotlin + Jetpack Compose + Room + WorkManager + Retrofit/OkHttp.

원칙:
- 화면/메뉴는 계약서 §3.0 구조 그대로(대시보드/기록입력 탭통합/돈군/할일·알림 2탭/보고서 그룹). '분만사' 만들지 말 것.
- §1 Base URL 환경분리(BuildConfig debug/release, 에뮬 10.0.2.2, 평문은 debug만 usesCleartextTraffic).
- §2 auth: OkHttp Authenticator로 401→refresh→재시도. Bearer 토큰.
- §3 devices: 로그인 직후 FCM 토큰 POST /devices{platform:"ANDROID"}, 로그아웃 시 DELETE.
- §4 오프라인: Room 스키마를 sync 엔티티(matings/farrowings/weanings/reproductive_events/health_events/piglet_events)와 1:1. WorkManager 백그라운드 sync. Pull 6엔티티.
- §3 보고서: group_by=breed 토글 + production-summary(국가 기준값 대비 표시). 국가분기·임계계산 재구현 0(백엔드 값 표시만).
- §5 Enum/단위/통화 하드코딩 0 → GET /farms/{id}/config 사용. 아이콘=Material Symbols 벡터(이모지 금지).
- insights: 이벤트 POST 응답의 insights[]는 배너로 렌더만(판정 재구현 금지).

규칙: 각 화면/기능 완료 시 테스트(가능 범위) + git commit. git push 금지. 불확실하면 계약서/OpenAPI 우선, 그래도 모호하면 그 지점 명시하고 진행(임의 추측 금지). CLAUDE.md/PROGRESS.md 있으면 갱신.
```

---

## 3. iOS 세션 프롬프트 (pigos-ios)

```
cd <pigos-ios> && claude --dangerously-skip-permissions
```
```
/loop docs/contract/ 의 mobile-integration-contract.md(SSOT) + openapi-v1.yaml(필드 스키마) + offline-sync-spec.md 를 정독하고, 웹과 동일 기능/화면을 빠짐없이 구현해. 스택: Swift + SwiftUI + Core Data(오프라인) + URLSession/Alamofire.

원칙:
- 화면/메뉴는 계약서 §3.0 구조 그대로(대시보드/기록입력 탭통합/돈군/할일·알림 2탭/보고서 그룹). '분만사' 만들지 말 것.
- §1 Base URL 환경분리(Debug/Release.xcconfig, 시뮬 localhost, ATS NSAllowsLocalNetworking은 debug만).
- §2 auth: URLSession retry/Alamofire interceptor로 401→refresh→재시도. Bearer 토큰.
- §3 devices: 로그인 직후 APNS→FCM 토큰 POST /devices{platform:"IOS"}, 로그아웃 시 DELETE.
- §4 오프라인: Core Data 스키마를 sync 엔티티와 1:1. BGTaskScheduler 백그라운드 sync. Pull 6엔티티.
- §3 보고서: group_by=breed 토글 + production-summary(국가 기준값 대비 표시). 국가분기·임계계산 재구현 0.
- §5 Enum/단위/통화 하드코딩 0 → GET /farms/{id}/config 사용. 아이콘=SF Symbols 벡터(이모지 금지).
- insights: 이벤트 POST 응답의 insights[]는 배너로 렌더만.

규칙: 각 화면/기능 완료 시 테스트(가능 범위) + git commit. git push 금지. 불확실하면 계약서/OpenAPI 우선, 모호하면 그 지점 명시하고 진행. CLAUDE.md/PROGRESS.md 갱신.
```

---

## 4. 검증 게이트 (릴리스 전)

- **공통 계약 검증(§8a, 플랫폼 무관, 1벌)**: login→Bearer→401 refresh→재시도 · `GET /farms/{id}/config` 단위·통화 · 이벤트 POST→PATCH→DELETE(상태 롤백) · `POST /sync` push/pull 왕복(6엔티티) · `POST /devices`→`DELETE`. **iOS·Android 결과가 같아야 함** — 다르면 글루 버그.
- **🆕 P0 검증 계약(2026-06-19, 모바일 클라 사전검증 + 422 폴백 동일)**: 분만 TB=BA+SB+MUM·출생체중≤3 · 이유두수 항등식(weaned==nursing−폐사−out+in) 422 · 이유체중 2~12 · 교배 동일날짜 409·웅돈 ACTIVE만 · 임신중 도폐사 사유필수 · 양자 거울레코드 자동생성(한쪽만 전송) · 비육 입식 5~50/출하≤200. (백엔드 검증결과 = 권위, 모바일은 즉시 UX피드백만.)
- **🆕 보고서 엔드포인트(2026-06-19)**: `GET /reports/{sow-status,farrowing,mortality,data-quality}` 응답 스키마 = 계약서 §보고서. 빈 농장/대량 데이터 양쪽에서 200·크래시 0 확인.
- **플랫폼별 글루(§8b)**: 네트워크 평문예외·푸시·로컬DB·백그라운드는 OS API가 달라 iOS/Android **각각** 검증.
- **검증 현황(백엔드/웹)**: ruff·tsc·i18n(1084×5)·build 그린 / pytest 379 · live E2E 30 통과 / vitest는 로컬 Node<20.12로 보류(`docs/verification/qa_qc_2026-06-19.md`). 모바일은 동일 계약을 단말에서 재검증.
- 릴리스 = 8a 공통 통과 + 8b 각각 통과 + 계약서 §6 갭(G1 푸시활성화/G4 실단말 sync/G5 이미지) closed 또는 "다음 버전" 합의.

## 5. 동시 실행 메모
- 두 세션은 서로 다른 레포라 **동시 실행 가능**. 같은 dev 백엔드를 보도록 Base URL만 맞춘다(에뮬 10.0.2.2 / 시뮬 localhost / 실기기 PC-LAN-IP).
- 계약 변경 시 §1 절차로 양 레포 재동기화 후 공지.
