"""룰 엔진이 emit 하는 cause/action 코드가 번역맵에 **전 로케일** 존재하는지 가드.

누락 시 `_label` 폴백이 raw 코드를 Title-Case 로 노출한다 → ko·zh 로케일에서도 영문이
그대로 보인다(QA i18n 갭). 새 rule 에 코드를 추가했으면 `app/engine/i18n.py` 의
`CAUSE_LABELS`/`ACTION_LABELS` 에도 등록해야 한다.

## 구조가 바뀌었다 (2026-08-26 회수)

번역맵이 `renderer.py` 의 `_CAUSE_EN`/`_CAUSE_KO`(en·ko 2개어)에서
`i18n.py` 의 `CAUSE_LABELS[code][locale]`(**7개어**)로 옮겨졌다.

★ 이 리팩터는 **운영 서버에만 있고 git 에는 없던 코드**였다. 서버 코드에 남은 주석이
  이유를 설명한다 — "예전엔 여기에 en/ko 만 있어서 비영어·비한국어 질문은 무엇을 묻든
  전부 dashboard 로 떨어졌다." 배포 시 덮어쓸 뻔한 것을 회수했다.

그래서 이 테스트도 2개어가 아니라 **SUPPORTED_LOCALES 전체**를 검사한다. 로케일이
늘어나면 자동으로 그것까지 요구한다 — 목록을 손으로 유지하지 않는다.
"""
import glob
import os
import re

from app.engine.i18n import ACTION_LABELS, CAUSE_LABELS, SUPPORTED_LOCALES

_RULES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "app", "engine", "rules")


def _emitted(kind: str) -> set[str]:
    """rules/*.py 에서 causes=[...]/actions=[...] 리터럴 코드 수집(멀티라인 포함)."""
    codes: set[str] = set()
    for path in glob.glob(os.path.join(_RULES_DIR, "*.py")):
        with open(path, encoding="utf-8") as f:
            src = f.read()
        for m in re.finditer(rf"{kind}\s*=\s*\[(.*?)\]", src, re.S):
            codes |= set(re.findall(r'"([a-z0-9_]+)"', m.group(1)))
    return codes


def _missing_locales(labels: dict, codes: set[str]) -> dict[str, list[str]]:
    """코드별로 어떤 로케일이 비었는지 — 어디를 채워야 하는지 바로 보이게."""
    out: dict[str, list[str]] = {}
    for code in sorted(codes):
        entry = labels.get(code)
        if entry is None:
            out[code] = ["(코드 자체 없음)"]
            continue
        gaps = [loc for loc in SUPPORTED_LOCALES if not entry.get(loc)]
        if gaps:
            out[code] = gaps
    return out


def test_all_emitted_cause_codes_translated():
    gaps = _missing_locales(CAUSE_LABELS, _emitted("causes"))
    assert not gaps, f"CAUSE_LABELS 번역 누락(코드→빈 로케일): {gaps}"


def test_all_emitted_action_codes_translated():
    gaps = _missing_locales(ACTION_LABELS, _emitted("actions"))
    assert not gaps, f"ACTION_LABELS 번역 누락(코드→빈 로케일): {gaps}"


def test_every_entry_covers_every_locale():
    """★ 한 로케일만 추가하는 드리프트 방지 — 등록된 코드는 전 로케일을 갖춰야 한다.

    예전 en/ko 2개어 시절의 `set(_CAUSE_EN) == set(_CAUSE_KO)` 검사를 대체한다."""
    for name, labels in (("CAUSE_LABELS", CAUSE_LABELS), ("ACTION_LABELS", ACTION_LABELS)):
        gaps = {
            code: [loc for loc in SUPPORTED_LOCALES if not entry.get(loc)]
            for code, entry in labels.items()
            if any(not entry.get(loc) for loc in SUPPORTED_LOCALES)
        }
        assert not gaps, f"{name} 로케일 불균형: {gaps}"


def test_supported_locales_is_not_silently_shrunk():
    """지원 로케일이 줄면 그 언어 사용자가 조용히 영문을 보게 된다.

    UI 는 8개어(ru 포함)지만 룰 엔진 번역은 7개어다 — ru 는 아직 없다.
    줄어드는 것만 막고, 늘리는 것은 자유롭게 둔다."""
    assert set(SUPPORTED_LOCALES) >= {"en", "ko", "zh", "es", "vi", "th", "pt"}, (
        f"지원 로케일이 줄었다: {SUPPORTED_LOCALES}")
