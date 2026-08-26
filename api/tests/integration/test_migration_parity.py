"""마이그레이션이 모델 스키마를 재현하는가 — 드리프트 가드.

## 왜 필요한가 (독립검증 2026-08-25)

통합 테스트는 `Base.metadata.create_all()` 로 스키마를 만든다. **모델대로 만들기 때문에
마이그레이션이 무엇을 빠뜨렸는지 알 수 없다.** 그래서 다음 상태가 오래 숨어 있었다:

    farms.data_origin / data_classification   모델 O · 운영 O(손으로) · 마이그레이션 **X**
    idx_matings_sow_date 등 by-sow 인덱스 4개  모델 O · 운영 O(손으로) · 마이그레이션 **X**
    idx_farms_classification                   모델 O · 운영 **X**    · 마이그레이션 **X**
    created_at NOT NULL 5개 테이블             모델 O · 운영 **X**    · 마이그레이션 **X**

★ 이게 왜 위험한가: **재해복구와 새 환경 구축은 마이그레이션만 돌린다.** 운영에만 손으로
  있는 것은 그때 재현되지 않는다 — "복구했는데 인덱스가 없어 대시보드가 느리다",
  "컬럼이 없어 앱이 죽는다"가 된다. 백업을 아무리 잘 떠도 스키마가 다르면 소용없다.

이 파일은 `alembic check` 를 테스트로 끌어와, **마이그레이션과 모델이 갈라지면 CI 가
잡도록** 한다. 값 검증이 아니라 구조 검증이라 값 비교로는 못 잡는 종류를 잡는다.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

API_ROOT = Path(__file__).resolve().parents[2]


def _run_alembic(*args: str) -> subprocess.CompletedProcess:
    """테스트 DB 를 대상으로 alembic 을 돌린다.

    ★ 별도 프로세스로 돌린다 — alembic 은 자체 엔진·이벤트루프를 만들어서
      pytest 의 async 세션과 같은 프로세스에서 섞으면 루프 충돌이 난다.
    """
    env = {**os.environ}
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=API_ROOT, env=env, capture_output=True, text=True, timeout=300,
    )


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL") and not (API_ROOT / ".env").exists(),
    reason="alembic 이 볼 DATABASE_URL 이 없음(단위 테스트 환경)",
)
def test_migrations_reproduce_the_model_schema():
    """★ `alembic check` 가 통과해야 한다 — 마이그레이션 head == 모델.

    실패하면 출력에 어떤 객체가 어긋났는지 나온다. 대응은 둘 중 하나다:
      · 마이그레이션이 빠뜨렸다  → 보정 마이그레이션을 추가한다(f3c6a8d0b2e4 참고)
      · 모델이 선언을 빠뜨렸다  → 모델 __table_args__ 에 선언한다

    ⚠️ `alembic/env.py` 의 `_UNCOMPARABLE_INDEXES` 로 도망가지 말 것. 그 목록은
       **표현식·부분 인덱스처럼 alembic 이 원리적으로 대조 못 하는 것**만 넣는 자리다.
       시끄럽다고 넣으면 그 객체의 드리프트를 영영 못 잡는다.
    """
    r = _run_alembic("check")
    assert r.returncode == 0, (
        "마이그레이션과 모델이 어긋났다 — 재해복구 시 스키마가 재현되지 않는다.\n"
        f"{r.stdout[-3000:]}\n{r.stderr[-3000:]}"
    )


def test_uncomparable_index_list_stays_small():
    """비교 제외 목록이 조용히 커지지 않게 — 커지면 가드가 무력해진다."""
    env_py = (API_ROOT / "alembic" / "env.py").read_text(encoding="utf-8")
    assert "_UNCOMPARABLE_INDEXES" in env_py, "제외 목록 정의가 사라졌다"
    block = env_py.split("_UNCOMPARABLE_INDEXES")[1].split("}")[0]
    entries = [ln for ln in block.split("\n") if ln.strip().startswith('"')]
    assert len(entries) <= 5, (
        f"비교 제외 인덱스가 {len(entries)}개다. 표현식·부분 인덱스만 넣어야 하며, "
        "늘어난다면 대부분 '모델에 선언을 추가'가 맞는 대응이다.")
