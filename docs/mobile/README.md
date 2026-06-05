# PigOS Mobile — Android 개발 가이드

> 이 문서는 `c:\dev\PigOS` 레포의 API·스펙을 기반으로 Android 앱을 개발하는 개발자를 위한 레퍼런스입니다.

---

## 문서 목록

| 파일 | 내용 |
|------|------|
| [01-tech-stack.md](01-tech-stack.md) | Android 기술 스택 + 의존성 + 아키텍처 |
| [02-auth-flow.md](02-auth-flow.md) | JWT 인증 플로우 + 토큰 관리 |
| [03-api-endpoints.md](03-api-endpoints.md) | 전체 API 엔드포인트 레퍼런스 |
| [04-screens.md](04-screens.md) | 화면 목록 + 웹→앱 매핑 |
| [05-offline-sync.md](05-offline-sync.md) | 오프라인 동기화 아키텍처 (Room + WorkManager) |
| [06-design-tokens.md](06-design-tokens.md) | 컬러·타이포·간격 디자인 토큰 |

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
