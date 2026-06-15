"""
Push 전송 서비스 — FCM HTTP v1 (G1).

설계 원칙(LLM 렌더러와 동일): 자격증명/라이브러리가 없으면 예외 없이 graceful skip.
- settings.fcm_project_id + fcm_credentials_path 둘 다 있어야 실제 전송.
- google-auth 미설치 시에도 import 깨지지 않게 lazy import → skip.
- 배포 시 활성화: `uv add google-auth` + 두 env 설정.

반환 PushResult(sent, skipped, reason)로 항상 결과를 보고 (예외 전파 안 함).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

_FCM_ENDPOINT = "https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
_SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]


@dataclass
class PushResult:
    sent: int
    skipped: int
    reason: str | None = None


def _is_configured() -> bool:
    return bool(settings.fcm_project_id and settings.fcm_credentials_path)


def _access_token() -> str | None:
    """서비스 계정으로 OAuth2 액세스 토큰 발급. 실패/미설치 시 None."""
    try:
        from google.auth.transport.requests import Request  # type: ignore
        from google.oauth2 import service_account  # type: ignore
    except ImportError:
        log.warning("push: google-auth 미설치 — 푸시 skip (uv add google-auth 필요)")
        return None
    try:
        creds = service_account.Credentials.from_service_account_file(
            settings.fcm_credentials_path, scopes=_SCOPES,
        )
        creds.refresh(Request())
        return creds.token
    except Exception as e:  # noqa: BLE001
        log.error("push: 자격증명 로드 실패 — %s", e)
        return None


async def send_push(
    tokens: list[str], title: str, body: str, data: dict | None = None,
) -> PushResult:
    """주어진 토큰들에 푸시 전송. 미설정/미설치/토큰없음이면 skip."""
    if not tokens:
        return PushResult(sent=0, skipped=0, reason="no_tokens")
    if not _is_configured():
        return PushResult(sent=0, skipped=len(tokens), reason="fcm_not_configured")

    token = _access_token()
    if not token:
        return PushResult(sent=0, skipped=len(tokens), reason="no_credentials")

    url = _FCM_ENDPOINT.format(project_id=settings.fcm_project_id)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    sent = 0
    async with httpx.AsyncClient(timeout=10) as client:
        for tok in tokens:
            payload = {
                "message": {
                    "token": tok,
                    "notification": {"title": title, "body": body},
                    "data": {k: str(v) for k, v in (data or {}).items()},
                }
            }
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    sent += 1
                else:
                    log.warning("push: FCM %s — %s", resp.status_code, resp.text[:200])
            except Exception as e:  # noqa: BLE001 — 한 토큰 실패가 전체를 막지 않게
                log.error("push: 전송 실패 token=…%s err=%s", tok[-6:], e)
    return PushResult(sent=sent, skipped=len(tokens) - sent)
