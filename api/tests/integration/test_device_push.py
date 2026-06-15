"""
Device 등록 + Push fallback 테스트 (G1/G2) — pigos_test (Docker).
푸시는 미설정 환경이므로 graceful skip 경로를 검증 (외부 호출 없음).
"""
from app.db.models.platform import User
from app.services import device_service, push_service


class TestDeviceRegister:
    async def test_register_and_list(self, db, test_user: User):
        d = await device_service.register_device(db, test_user.id, "ANDROID", "tok-aaa", "1.0.0")
        assert d.token == "tok-aaa"
        assert d.platform == "ANDROID"
        devices = await device_service.list_user_devices(db, test_user.id)
        assert any(x.token == "tok-aaa" for x in devices)

    async def test_register_upsert_same_token(self, db, test_user: User):
        d1 = await device_service.register_device(db, test_user.id, "ANDROID", "tok-dup", "1.0.0")
        d2 = await device_service.register_device(db, test_user.id, "IOS", "tok-dup", "2.0.0")
        # 같은 토큰 → 같은 row 갱신 (중복 생성 안 함)
        assert d1.id == d2.id
        assert d2.platform == "IOS"
        assert d2.app_version == "2.0.0"

    async def test_active_tokens_and_unregister(self, db, test_user: User):
        await device_service.register_device(db, test_user.id, "ANDROID", "tok-x", None)
        tokens = await device_service.active_tokens_for_users(db, [test_user.id])
        assert "tok-x" in tokens
        removed = await device_service.unregister_token(db, test_user.id, "tok-x")
        assert removed == 1
        tokens2 = await device_service.active_tokens_for_users(db, [test_user.id])
        assert "tok-x" not in tokens2


class TestPushFallback:
    async def test_no_tokens(self):
        res = await push_service.send_push([], "t", "b")
        assert res.sent == 0
        assert res.reason == "no_tokens"

    async def test_not_configured_skips(self):
        # 테스트 환경엔 FCM 미설정 → 외부 호출 없이 skip
        res = await push_service.send_push(["tok-1", "tok-2"], "t", "b")
        assert res.sent == 0
        assert res.skipped == 2
        assert res.reason in ("fcm_not_configured", "no_credentials")
