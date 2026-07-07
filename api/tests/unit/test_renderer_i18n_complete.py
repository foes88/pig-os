"""룰 엔진이 emit하는 cause/action 코드가 renderer 번역맵(en·ko)에 전부 존재하는지 가드.

누락 시 _label 폴백이 raw 코드를 Title-Case로 노출 → ko 로케일에서도 영문 노출(QA i18n 갭).
이 테스트가 깨지면: 새 rule에 추가한 cause/action 코드를 renderer.py의 _CAUSE_*/_ACTION_*에 등록할 것.
"""
import glob
import os
import re

from app.engine.renderer import _ACTION_EN, _ACTION_KO, _CAUSE_EN, _CAUSE_KO

_RULES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "app", "engine", "rules")


def _emitted(kind: str) -> set[str]:
    """rules/*.py에서 causes=[...]/actions=[...] 리터럴 코드 수집(멀티라인 포함)."""
    codes: set[str] = set()
    for path in glob.glob(os.path.join(_RULES_DIR, "*.py")):
        with open(path, encoding="utf-8") as f:
            src = f.read()
        for m in re.finditer(rf"{kind}\s*=\s*\[(.*?)\]", src, re.S):
            codes |= set(re.findall(r'"([a-z0-9_]+)"', m.group(1)))
    return codes


def test_all_emitted_cause_codes_translated():
    emitted = _emitted("causes")
    missing_en = sorted(emitted - set(_CAUSE_EN))
    missing_ko = sorted(emitted - set(_CAUSE_KO))
    assert not missing_en, f"_CAUSE_EN 누락: {missing_en}"
    assert not missing_ko, f"_CAUSE_KO 누락: {missing_ko}"


def test_all_emitted_action_codes_translated():
    emitted = _emitted("actions")
    missing_en = sorted(emitted - set(_ACTION_EN))
    missing_ko = sorted(emitted - set(_ACTION_KO))
    assert not missing_en, f"_ACTION_EN 누락: {missing_en}"
    assert not missing_ko, f"_ACTION_KO 누락: {missing_ko}"


def test_cause_maps_en_ko_same_keys():
    """en/ko 맵 키셋 동기(한쪽만 추가하는 드리프트 방지)."""
    assert set(_CAUSE_EN) == set(_CAUSE_KO), {
        "en_only": sorted(set(_CAUSE_EN) - set(_CAUSE_KO)),
        "ko_only": sorted(set(_CAUSE_KO) - set(_CAUSE_EN)),
    }


def test_action_maps_en_ko_same_keys():
    assert set(_ACTION_EN) == set(_ACTION_KO), {
        "en_only": sorted(set(_ACTION_EN) - set(_ACTION_KO)),
        "ko_only": sorted(set(_ACTION_KO) - set(_ACTION_EN)),
    }
