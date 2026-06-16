# docs/verification — 검증 리포트 모음 (Codex 진입점)

모바일↔백엔드 검증 결과·재현 방법·재검증 요청을 날짜별로 둔다. Codex는 여기부터 본다.

| 날짜 | 리포트 | 요지 |
|------|--------|------|
| 2026-06-16 | [sync-env-verification](2026-06-16_sync-env-verification.md) | `/sync` 영속 버그 4종 수정+회귀가드, 백엔드 pytest 283 통과, 라이브 E2E 그린. iOS는 Mac/CI 검증 대기. |

## 빠른 재검증
```powershell
cd c:\dev\pigos\api
uv run pytest -q                                   # 전체 (283 passed)
uv run pytest tests/integration/test_sync_farrowing.py -v   # /sync 회귀 가드 (3)
```
> 처음 실행이 errors 나면: `lc_messages='C'` + `pigos_test` DB + `alembic upgrade head` (리포트 §2 참고).
