"""F2 — 리프레시 토큰 회전 후 재사용 감지 시 패밀리 전체 회수(OWASP).

기존: 회전된(revoked) RT0를 재사용하면 단일 토큰만 401이고 활성 RT1은 살아남아,
탈취자·피해자가 동시에 갱신을 이어갈 수 있었다. 이제 재사용 감지 시 해당 사용자
활성 리프레시 토큰을 모두 회수해 재로그인을 강제한다.
"""
import pytest

from app.core.exceptions import UnauthorizedError
from app.db.models.platform import User
from app.services.auth_service import issue_tokens, refresh_tokens

pytestmark = pytest.mark.anyio


async def test_normal_rotation_chain_works(db, test_user: User):
    t0 = await issue_tokens(db, test_user)
    t1 = await refresh_tokens(db, t0.refresh_token)
    assert t1.refresh_token and t1.refresh_token != t0.refresh_token
    # 정상 후속 회전 1회 더 성공
    t2 = await refresh_tokens(db, t1.refresh_token)
    assert t2.refresh_token


async def test_reuse_of_rotated_token_revokes_family(db, test_user: User):
    t0 = await issue_tokens(db, test_user)
    t1 = await refresh_tokens(db, t0.refresh_token)  # RT0 회전 → revoked, RT1 발급

    # RT0(회전 완료) 재사용 → 탈취 의심 → 재사용 감지 거부
    with pytest.raises(UnauthorizedError):
        await refresh_tokens(db, t0.refresh_token)

    # 패밀리 회수로 RT1도 더 이상 사용 불가(과거엔 살아 있었음)
    with pytest.raises(UnauthorizedError):
        await refresh_tokens(db, t1.refresh_token)
