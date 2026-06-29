"""F3 — 로그인 계정 열거(타이밍 오라클) 차단.

기존: 사용자 미존재 시 bcrypt를 건너뛰어 응답이 빨라(~210ms 차) 계정 존재가 누출됐다.
이제 미존재 계정도 더미 해시로 bcrypt 1회를 수행해 응답시간을 맞춘다.
타이밍 측정은 flaky하므로, bcrypt 검증이 실제로 호출되는지를 결정론적으로 검증.
"""
import pytest

import app.services.auth_service as svc
from app.core.exceptions import UnauthorizedError
from app.db.models.platform import User

pytestmark = pytest.mark.anyio


async def test_unknown_user_still_runs_bcrypt(db, monkeypatch):
    calls = []
    real = svc.verify_password
    monkeypatch.setattr(svc, "verify_password",
                        lambda pw, h: (calls.append(h), real(pw, h))[1])
    with pytest.raises(UnauthorizedError):
        await svc.authenticate(db, "no_such_user_zzz", "whatever")
    assert calls == [svc._DUMMY_PW_HASH], "미존재 계정도 더미 해시로 bcrypt 1회 수행해야 함"


async def test_existing_user_wrong_password_runs_bcrypt_once(db, test_user: User, monkeypatch):
    calls = []
    real = svc.verify_password
    monkeypatch.setattr(svc, "verify_password",
                        lambda pw, h: (calls.append(h), real(pw, h))[1])
    with pytest.raises(UnauthorizedError):
        await svc.authenticate(db, test_user.username, "WrongPass!")
    assert calls == [test_user.password_hash], "존재 계정도 bcrypt 정확히 1회"
