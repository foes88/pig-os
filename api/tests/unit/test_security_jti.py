"""
토큰 jti 유일성 — P0/P1 근인(토큰 중복 → RefreshToken.token_hash UNIQUE 충돌 500) 회귀 가드.

jti(고유 클레임)가 없으면 같은 유저·같은 초에 만든 토큰이 바이트 동일 → 같은 token_hash
→ IntegrityError 500(refresh 항상·로그인 동시성). jti로 매 토큰을 유일하게 만들어 차단.
"""
from uuid import uuid4

from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)


def _decode(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


class TestJtiUniqueness:
    def test_two_refresh_tokens_same_user_differ(self):
        uid = uuid4()
        t1 = create_refresh_token(uid)
        t2 = create_refresh_token(uid)
        assert t1 != t2, "같은 유저 refresh 토큰이 동일하면 token_hash 충돌(500 근인)"

    def test_two_access_tokens_same_user_differ(self):
        uid, org = uuid4(), uuid4()
        a1 = create_access_token(uid, org, ["FARM_OWNER"])
        a2 = create_access_token(uid, org, ["FARM_OWNER"])
        assert a1 != a2

    def test_refresh_token_has_jti(self):
        payload = _decode(create_refresh_token(uuid4()))
        assert "jti" in payload and payload["jti"]

    def test_access_token_has_jti(self):
        payload = _decode(create_access_token(uuid4(), uuid4(), ["FARM_OWNER"]))
        assert "jti" in payload and payload["jti"]

    def test_jti_is_unique_per_call(self):
        uid = uuid4()
        jtis = {_decode(create_refresh_token(uid))["jti"] for _ in range(20)}
        assert len(jtis) == 20, "jti가 호출마다 유일해야 함"

    def test_refresh_token_still_decodes_to_user(self):
        # jti 추가가 기존 디코드(sub 추출)를 깨지 않는지
        uid = uuid4()
        assert decode_refresh_token(create_refresh_token(uid)) == str(uid)


# ── 깨진 해시 (2026-08-25) ───────────────────────────────────────────────────

def test_malformed_hash_fails_closed_instead_of_raising():
    """★ 검증 불가능한 해시는 **예외가 아니라 인증 실패**여야 한다.

    bcrypt.checkpw 는 형식이 아닌 문자열에 ValueError('Invalid salt') 를 던진다.
    그대로 두면 탈퇴 계정(익명화 시 bcrypt 가 아닌 자리표시 해시가 들어간다)이나
    손상된 행에서 **인증 실패가 아니라 500** 이 난다.

    fail-closed 여야 한다 — 검증할 수 없으면 통과시키지 않는다."""
    from app.core.security import verify_password

    for broken in ("", "not-a-hash", "!deleted!abc123", "$2b$xx$short", "$2b$"):
        assert verify_password("anything", broken) is False, f"{broken!r} 에서 실패해야 한다"


def test_valid_hash_still_works():
    """폴백이 정상 경로를 망가뜨리지 않았는지."""
    from app.core.security import hash_password, verify_password

    h = hash_password("Correct-Horse-1")
    assert verify_password("Correct-Horse-1", h) is True
    assert verify_password("wrong", h) is False
