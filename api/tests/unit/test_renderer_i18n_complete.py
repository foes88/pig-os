"""룰 엔진이 emit하는 cause/action 코드가 i18n 카탈로그에 **7개 로케일 전부** 존재하는지 가드.

누락 시 label() 폴백이 raw 코드를 Title-Case로 노출하거나 영어로 새어나간다.
(실제로 이 가드가 en/ko 2종만 검사하던 동안, zh/es/vi/th/pt 는 전부 영어로 폴백되고 있었다.)

이 테스트가 깨지면: 새 rule에 추가한 cause/action 코드를 app/engine/i18n.py 의
CAUSE_LABELS / ACTION_LABELS 에 **SUPPORTED_LOCALES 전부** 채워서 등록할 것.
"""
import glob
import os
import re

from app.engine.i18n import (
    ACTION_LABELS,
    CAUSE_LABELS,
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
    UI_LABELS,
    label,
    normalize_locale,
)

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


def _missing(catalog: dict[str, dict[str, str]], emitted: set[str]) -> dict[str, list[str]]:
    """로케일별 누락 코드. 코드 자체가 없으면 전 로케일 누락으로 잡힌다."""
    out: dict[str, list[str]] = {}
    for loc in SUPPORTED_LOCALES:
        gaps = sorted(c for c in emitted if not (catalog.get(c) or {}).get(loc))
        if gaps:
            out[loc] = gaps
    return out


def test_all_emitted_cause_codes_translated_in_every_locale():
    assert not _missing(CAUSE_LABELS, _emitted("causes"))


def test_all_emitted_action_codes_translated_in_every_locale():
    assert not _missing(ACTION_LABELS, _emitted("actions"))


def test_catalog_entries_cover_every_supported_locale():
    """카탈로그에 등록된 코드는 전부 7개 로케일을 채워야 한다(한 언어만 추가하는 드리프트 방지)."""
    gaps: dict[str, list[str]] = {}
    for name, catalog in (
        ("CAUSE_LABELS", CAUSE_LABELS),
        ("ACTION_LABELS", ACTION_LABELS),
        ("UI_LABELS", UI_LABELS),
    ):
        for code, entry in catalog.items():
            miss = sorted(set(SUPPORTED_LOCALES) - {k for k, v in entry.items() if v})
            if miss:
                gaps[f"{name}.{code}"] = miss
    assert not gaps


def test_supported_locales_match_app_languages():
    """앱/웹이 지원하는 7개 언어와 동기. 언어를 늘리면 카탈로그도 같이 늘려야 한다."""
    assert set(SUPPORTED_LOCALES) == {"en", "ko", "zh", "es", "vi", "th", "pt"}
    assert DEFAULT_LOCALE == "en"


def test_normalize_locale_folds_variants_and_unknowns():
    assert normalize_locale("pt-BR") == "pt"
    assert normalize_locale("zh_Hans") == "zh"
    assert normalize_locale("es-419") == "es"
    assert normalize_locale("TH") == "th"
    assert normalize_locale("ru") == DEFAULT_LOCALE   # 미지원 언어는 영어 폴백
    assert normalize_locale(None) == DEFAULT_LOCALE
    assert normalize_locale("") == DEFAULT_LOCALE


def test_label_falls_back_to_en_then_humanized_code():
    catalog = {"only_en": {"en": "Only English"}}
    assert label(catalog, "only_en", "th") == "Only English"      # 로케일 누락 → en
    assert label(catalog, "brand_new_code", "ko") == "Brand New Code"  # 미등록 → humanize
