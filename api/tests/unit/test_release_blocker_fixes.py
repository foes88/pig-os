"""
출시 블로커 수정 회귀 가드(순수 — DB/HTTP 불필요).

- B7: /sows/removals(정적)가 /{sow_id}(동적)보다 먼저 등록돼야 함(아니면 uuid_parsing 422).
- 날짜수정 500: 이벤트 Update 스키마의 date 필드는 model_dump(mode="json")에서 ISO 문자열
  (JSONB audit에 안전). date 객체로 남으면 직렬화 500.
"""
from datetime import date

from app.routers.base.sows import router as sows_router
from app.schemas.events import FarrowingUpdate, MatingUpdate, WeaningUpdate


def _get_paths_in_order() -> list[str]:
    """sows 라우터의 GET 경로를 등록 순서대로."""
    paths = []
    for r in sows_router.routes:
        methods = getattr(r, "methods", set()) or set()
        if "GET" in methods:
            paths.append(r.path)
    return paths


class TestRemovalsRouteOrder:
    def test_removals_registered_before_sow_id(self):
        # 라우트 path는 prefix 포함(.../sows/removals, .../sows/{sow_id}).
        paths = _get_paths_in_order()
        rem = next((i for i, p in enumerate(paths) if p.endswith("/removals")), None)
        sid = next((i for i, p in enumerate(paths) if p.endswith("/{sow_id}")), None)
        assert rem is not None, f"list_removals 라우트 누락: {paths}"
        assert sid is not None, f"get_sow 라우트 누락: {paths}"
        assert rem < sid, "정적 /removals 가 동적 /{sow_id} 보다 먼저 등록돼야 함(B7 422 방지)"


class TestUpdateDateSerialization:
    """date 필드가 mode='json'에서 문자열이어야 JSONB audit 직렬화 안전(날짜수정 500 방지)."""

    def test_farrowing_update_date_is_str_json(self):
        dumped = FarrowingUpdate(farrowing_date=date(2026, 5, 5)).model_dump(
            mode="json", exclude_unset=True
        )
        assert isinstance(dumped["farrowing_date"], str)

    def test_mating_update_date_is_str_json(self):
        dumped = MatingUpdate(mating_date=date(2026, 1, 10)).model_dump(
            mode="json", exclude_unset=True
        )
        assert isinstance(dumped["mating_date"], str)

    def test_weaning_update_date_is_str_json(self):
        dumped = WeaningUpdate(weaning_date=date(2026, 5, 26)).model_dump(
            mode="json", exclude_unset=True
        )
        assert isinstance(dumped["weaning_date"], str)

    def test_json_serializable(self):
        # 실제 json.dumps가 가능한지(JSONB 직렬화 대리)
        import json
        d = FarrowingUpdate(farrowing_date=date(2026, 5, 5)).model_dump(mode="json", exclude_unset=True)
        json.dumps(d)  # raise 없어야 함
