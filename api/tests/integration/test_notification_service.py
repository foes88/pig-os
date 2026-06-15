"""Notification 서비스 통합 테스트 (P12-6) — pigos_test (Docker)."""
from app.db.models.ops import Notification
from app.db.models.platform import Farm, User
from app.services import notification_service


async def _add(db, user, farm, title="알림", read=False, type_="IN_APP"):
    n = Notification(
        farm_id=farm.id, user_id=user.id, type=type_, title=title,
        body="본문", severity="WARNING",
    )
    db.add(n)
    await db.flush()
    return n


class TestList:
    async def test_list_and_unread_count(self, db, test_farm: Farm, test_user: User):
        await _add(db, test_user, test_farm, "a")
        await _add(db, test_user, test_farm, "b")
        rows, unread, total = await notification_service.list_notifications(db, test_user.id)
        assert total >= 2
        assert unread >= 2
        assert len(rows) >= 2

    async def test_push_type_excluded(self, db, test_farm: Farm, test_user: User):
        await _add(db, test_user, test_farm, "push", type_="PUSH")
        rows, _u, _t = await notification_service.list_notifications(db, test_user.id)
        assert all(r.title != "push" for r in rows)


class TestMarkRead:
    async def test_mark_one_read(self, db, test_farm: Farm, test_user: User):
        n = await _add(db, test_user, test_farm, "c")
        updated = await notification_service.mark_read(db, test_user.id, n.id)
        assert updated == 1
        await db.refresh(n)
        assert n.read_at is not None
        # 두 번째 호출은 이미 읽음 → 0
        assert await notification_service.mark_read(db, test_user.id, n.id) == 0

    async def test_mark_all_read(self, db, test_farm: Farm, test_user: User):
        await _add(db, test_user, test_farm, "d")
        await _add(db, test_user, test_farm, "e")
        updated = await notification_service.mark_all_read(db, test_user.id, farm_id=test_farm.id)
        assert updated >= 2
        _r, unread, _t = await notification_service.list_notifications(
            db, test_user.id, farm_id=test_farm.id
        )
        assert unread == 0
