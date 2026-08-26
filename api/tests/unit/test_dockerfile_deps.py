"""Dockerfile 이 pyproject 의 의존성을 실제로 설치하는가.

## 배경 (2026-08-26 배포 실패)

Dockerfile 이 `pyproject.toml` 을 COPY 해놓고 **읽지 않고 패키지를 손으로 나열**하고
있었다. 그래서 pyproject 에 의존성을 추가해도 이미지에 들어가지 않았다.

    RUN uv pip install --system --no-cache-dir \\
        "fastapi[standard]" "sqlalchemy[asyncio]" asyncpg alembic ...   ← 손으로 나열

★ 이 결함은 **배포한 뒤에야 드러난다.** 로컬·CI 는 `uv sync` 로 pyproject 를 읽으므로
  전부 통과하고, 운영에서만 `ModuleNotFoundError` 로 컨테이너가 크래시 루프에 빠진다.
  실제로 markdown 추가 후 배포에서 그렇게 죽었다(헬스체크 502 → 롤백).
  같은 이유로 `boto3`(S3 백업)·`tzdata`(타임존)도 조용히 빠져 있었다.

목록 이중관리는 반드시 어긋난다. 하나의 소스만 두고, 그 규칙을 여기서 강제한다.
"""
import re
from pathlib import Path

_API = Path(__file__).resolve().parents[2]
_DOCKERFILE = _API / "Dockerfile"
_PYPROJECT = _API / "pyproject.toml"


def _dockerfile() -> str:
    return _DOCKERFILE.read_text(encoding="utf-8").replace("\r\n", "\n")


def _declared_deps() -> set[str]:
    """pyproject [project].dependencies 의 패키지명(extras·버전 제거).

    ★ 줄 단위로 읽는다. `src.split("]")` 로 자르면 `"fastapi[standard]"` 의 extras
      대괄호에서 먼저 잘려 목록이 통째로 비어버린다(실제로 그렇게 틀렸다).
    """
    text = _PYPROJECT.read_text(encoding="utf-8")
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip() == "dependencies = [")
    names = set()
    for ln in lines[start + 1:]:
        if ln.strip() == "]":
            break
        m = re.search(r'"([^"]+)"', ln)
        if m:
            names.add(re.split(r"[<>=!~\[]", m.group(1), maxsplit=1)[0].strip().lower())
    return names


def test_dockerfile_installs_from_pyproject():
    """★ 손으로 나열하지 않고 pyproject 를 읽어야 한다.

    이걸 어기면 의존성을 추가해도 이미지에 안 들어가고, **배포 후에야** 죽는다."""
    df = _dockerfile()
    install_lines = [ln for ln in df.split("\n") if "pip install" in ln and "uv" in ln]
    assert install_lines, "uv pip install 라인을 찾지 못했다"

    joined = " ".join(install_lines)
    assert "-r pyproject.toml" in joined or "--requirements" in joined, (
        "Dockerfile 이 pyproject 를 읽지 않는다. 패키지를 손으로 나열하면 pyproject 에\n"
        "의존성을 추가해도 이미지에 들어가지 않아 **배포 후 ModuleNotFoundError** 로 죽는다.\n"
        f"현재: {joined.strip()}")


def test_no_hand_listed_packages_in_install_line():
    """설치 라인에 패키지명이 박혀 있으면 다시 이중관리가 된다."""
    df = _dockerfile()
    for ln in df.split("\n"):
        if "pip install" not in ln or "uv" not in ln:
            continue
        # uv 자체 설치(pip install uv)는 예외 — 부트스트랩이다.
        if re.search(r"pip install\s+(--[\w-]+\s+)*uv\b", ln):
            continue
        for pkg in ("fastapi", "sqlalchemy", "asyncpg", "alembic", "redis", "arq"):
            assert pkg not in ln.lower(), (
                f"설치 라인에 '{pkg}' 가 하드코딩돼 있다 — pyproject 와 이중관리가 된다:\n  {ln.strip()}")


def test_runtime_critical_deps_are_declared():
    """운영에서 실제로 import 하는 것들이 pyproject 에 있는지.

    과거에 이미지에서 빠져 있던 것들이라 명시적으로 잠근다."""
    deps = _declared_deps()
    for pkg in ("markdown", "boto3", "tzdata", "fastapi", "sqlalchemy", "asyncpg", "alembic"):
        assert pkg in deps, f"pyproject dependencies 에 {pkg} 누락"


def test_build_context_keeps_pyproject():
    """pyproject 를 COPY 하지 않으면 -r 설치가 실패한다."""
    assert "COPY pyproject.toml" in _dockerfile()
