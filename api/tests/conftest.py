"""
공통 fixtures — unit/integration 양쪽에서 사용.
Integration DB fixture는 tests/integration/conftest.py에 분리.
"""
import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"
