# PigOS Mobile — Android 개발 가이드

> 이 문서는 `c:\dev\PigOS` 레포의 API·스펙을 기반으로 Android 앱을 개발하는 개발자를 위한 레퍼런스입니다.
>
> ⛔ **API/계약의 단일 기준(SSOT)은 [../mobile-integration-contract.md](../mobile-integration-contract.md)** 입니다.
> (라이브 라우트 기반 — 모돈상태 v2 / boars / 알림 / tasks / sync / 푸시 디바이스 전부 정확)
> 아래 03/MOBILE_API_CHANGES는 stale → DEPRECATED. 새 작업은 반드시 계약서 먼저 읽고 시작.

---

## 문서 목록

| 파일 | 상태 | 내용 |
|------|------|------|
| **[../mobile-integration-contract.md](../mobile-integration-contract.md)** | ✅ **SSOT** | API 계약·enum·sync·푸시·검증 매트릭스 (이것 먼저) |
| [01-tech-stack.md](01-tech-stack.md) | 참고 | Android 기술 스택 + 의존성 + 아키텍처 |
| [02-auth-flow.md](02-auth-flow.md) | 참고 | JWT 인증 플로우 (계약서 §2와 교차확인) |
| [03-api-endpoints.md](03-api-endpoints.md) | ⛔ DEPRECATED | 모돈 상태값·엔드포인트 불일치 → 계약서로 대체 |
| [04-screens.md](04-screens.md) | 참고 | 화면은 `docs/SCREEN_MENU_SPEC.md` 우선 |
| [05-offline-sync.md](05-offline-sync.md) | 참고 | 상세는 `docs/specs/2026-05-19_offline-sync-spec.md` 우선 |
| [06-design-tokens.md](06-design-tokens.md) | 참고 | 컬러·타이포·간격 디자인 토큰 |
| [MOBILE_API_CHANGES_2026-06-09.md](MOBILE_API_CHANGES_2026-06-09.md) | ⛔ DEPRECATED | 0adfa23 기준 — 이후 반영 완료, 계약서로 대체 |

---

## 핵심 원칙

1. **API 공용** — 웹(Next.js)과 동일한 FastAPI 사용. `BASE_URL/api/v1/`
2. **오프라인 퍼스트** — Room에 먼저 저장 → WorkManager로 백그라운드 동기화
3. **farm_id 격리** — 모든 데이터 요청에 `farm_id` 필수. 테넌트 보안 핵심
4. **JWT 인터셉터** — 모든 요청에 `Authorization: Bearer {accessToken}` 자동 첨부
5. **충돌 처리** — Last-Write-Wins 기본, 서버가 최종 판단

---

## API 서버

| 환경 | URL |
|------|-----|
| 개발 | `http://10.0.2.2:8000` (에뮬레이터 → 로컬호스트) |
| 개발 (실기기) | `http://[로컬IP]:8000` |
| 프로덕션 | `https://api.pigos.io` (배포 후) |

OpenAPI 스펙: `docs/api/openapi-v1.yaml`
