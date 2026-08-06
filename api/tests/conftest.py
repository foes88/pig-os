"""
공통 fixtures — unit/integration 양쪽에서 사용.
Integration DB fixture는 tests/integration/conftest.py에 분리.
"""
import pytest

from app.core.config import settings


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def _allow_kr_signup(monkeypatch):
    """테스트/개발 환경 = 대표 확인용으로 KR 가입 허용(운영 기본 차단).
    KR을 기본 법역으로 쓰는 consent 테스트가 signup_blocked(451)로 깨지지 않도록.
    KR 차단 자체 검증은 jurisdiction.resolve 순수 레벨에서 별도로 한다."""
    monkeypatch.setattr(settings, "allow_kr_signup", True)
