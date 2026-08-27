#!/usr/bin/env python
"""PigPlan `TS_INS_AI_RULES` ↔ 스냅샷 diff — **관측 전용**.

## 무엇을 하는가

2026-06-23 스냅샷(`handoff/pigplan-rules/pigplan_ai_rules.json`) 이후 레거시 운영 룰에
무엇이 **추가·변경·삭제**됐는지만 탐지한다. 그게 전부다.

## 무엇을 하지 않는가 — 이게 더 중요하다

    ❌ 자동 동기화        ❌ 자동 seed        ❌ PigOS 반영
    ❌ 스냅샷 자동 갱신    ❌ DB 쓰기(Oracle·PostgreSQL 양쪽 모두)

★ **이 스크립트는 PigOS 개발의 dependency 가 아니다.** 못 돌려도 개발은 진행한다.
  Oracle 이 죽어 있거나 자격증명이 없어도 그냥 "확인 못 함"으로 끝난다.

## 왜 자동 반영을 금지하는가

레거시 룰은 **AI 시스템 프롬프트에 주입되는 텍스트**(MD/JSON)다. PigOS 는 Rule Engine 이
판정하고 LLM 은 번역만 한다 — 구조가 다르다. 그리고 136개 중 상당수가 KR 전용 임계값이라
그대로 끌어오면 **8개 법역에 한국 기준이 새어 들어간다.**

레거시는 "무엇이 필요한가"의 **지식 참고용**이고, 구현은 PigOS 네이티브로 한다
(handoff/pigplan-rules/README.md).

## 임계값 태그

숫자가 바뀐 변경이 PigOS 검토에 가장 중요하므로 `[THRESHOLD]` 로 따로 표시한다.
설명 문구만 다듬은 변경과 기준값이 움직인 변경은 무게가 다르다.

## 사용

    cd api
    uv run --with oracledb python scripts/pigplan_rules_diff.py
    uv run --with oracledb python scripts/pigplan_rules_diff.py --json out.json

    ORACLE_PW 는 api/.env 또는 환경변수. 미설정 시 그냥 안내하고 종료한다(실패 아님).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

_API = Path(__file__).resolve().parent.parent
SNAPSHOT = _API.parent / "handoff" / "pigplan-rules" / "pigplan_ai_rules.json"
SNAPSHOT_DATE = "2026-06-23"

# 비교 대상 필드 — updDt 는 제외한다(내용이 같은데 타임스탬프만 바뀌는 경우가 많다).
_COMPARED = ("ruleGroup", "ruleCode", "ruleNm", "ruleType", "useYn", "description", "ruleContent")

# 룰 본문에서 뽑는 수치. 임계값 변화 판정에 쓴다.
# 버전/일자처럼 보이는 것은 제외한다(2026-04-10 같은 값이 임계값으로 잡히면 노이즈가 된다).
_NUM = re.compile(r"(?<![\d.\-])(\d+(?:\.\d+)?)(?![\d.]*[-/]\d)")


def _load_dotenv() -> None:
    """api/.env 를 읽는다 — 비밀값은 코드에 두지 않는다(harvest_import.py 와 동일 규칙)."""
    env = _API / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _key(row: dict) -> str:
    """식별자. ruleSeq 는 재생성될 수 있으므로 group+code 로 잡는다."""
    return f"{row.get('ruleGroup')}/{row.get('ruleCode')}"


def _hash(row: dict) -> str:
    payload = "\x1f".join(str(row.get(f) or "") for f in _COMPARED)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _numbers(text: str | None) -> list[str]:
    return _NUM.findall(text or "")


def _changed_fields(old: dict, new: dict) -> list[str]:
    return [f for f in _COMPARED if (old.get(f) or "") != (new.get(f) or "")]


def _is_threshold_change(old: dict, new: dict) -> bool:
    """본문·설명의 **숫자 집합**이 달라졌는가.

    ★ 문구만 다듬은 변경과 기준값이 움직인 변경을 가른다. 후자가 PigOS 검토 대상이다.
    """
    for f in ("ruleContent", "description"):
        if sorted(_numbers(old.get(f))) != sorted(_numbers(new.get(f))):
            return True
    return False


def _fetch_live() -> list[dict] | None:
    """운영 Oracle 에서 현재 룰을 읽는다. **읽기 전용.** 실패하면 None."""
    pw = os.getenv("ORACLE_PW")
    if not pw:
        print("  ORACLE_PW 미설정 — 라이브 조회를 건너뜁니다(실패 아님).", file=sys.stderr)
        print("  api/.env 에 ORACLE_PW 를 넣거나 환경변수로 주십시오.", file=sys.stderr)
        return None
    try:
        import oracledb
    except ImportError:
        print("  oracledb 미설치 — `uv run --with oracledb python ...` 로 실행하십시오.",
              file=sys.stderr)
        return None

    dsn = os.getenv(
        "ORACLE_DSN",
        "pigclouddb.c8ks4denaq5l.ap-northeast-2.rds.amazonaws.com:1521/PIGPLAN")
    user = os.getenv("ORACLE_USER", "pksu")
    try:
        with oracledb.connect(user=user, password=pw, dsn=dsn) as cn, cn.cursor() as cur:
            cur.execute(
                "SELECT RULE_SEQ, RULE_GROUP, RULE_CODE, RULE_NM, RULE_TYPE, USE_YN, "
                "       SORT_NO, DESCRIPTION, RULE_CONTENT, UPD_DT "
                "  FROM TS_INS_AI_RULES")
            cols = ("ruleSeq", "ruleGroup", "ruleCode", "ruleNm", "ruleType", "useYn",
                    "sortNo", "description", "ruleContent", "updDt")
            rows = []
            for rec in cur:
                d = {}
                for c, v in zip(cols, rec, strict=True):
                    # CLOB 은 read() 해야 문자열이 된다
                    d[c] = v.read() if hasattr(v, "read") else (
                        v.isoformat() if hasattr(v, "isoformat") else v)
                rows.append(d)
            return rows
    except Exception as e:  # noqa: BLE001 — 관측 실패는 개발을 막지 않는다
        print(f"  Oracle 조회 실패({type(e).__name__}): {str(e)[:160]}", file=sys.stderr)
        return None


def diff(base: list[dict], live: list[dict]) -> dict:
    b = {_key(r): r for r in base}
    live_map = {_key(r): r for r in live}

    added = sorted(set(live_map) - set(b))
    deleted = sorted(set(b) - set(live_map))
    changed, unchanged = [], 0
    for k in sorted(set(b) & set(live_map)):
        if _hash(b[k]) == _hash(live_map[k]):
            unchanged += 1
            continue
        changed.append({
            "key": k,
            "changed_fields": _changed_fields(b[k], live_map[k]),
            "old_hash": _hash(b[k]),
            "new_hash": _hash(live_map[k]),
            "threshold": _is_threshold_change(b[k], live_map[k]),
            "title": live_map[k].get("ruleNm"),
            "modified_at": live_map[k].get("updDt"),
        })
    return {
        "baseline": SNAPSHOT_DATE,
        "counts": {"added": len(added), "changed": len(changed),
                   "deleted": len(deleted), "unchanged": unchanged},
        "added": [{"key": k, "title": live_map[k].get("ruleNm"),
                   "category": live_map[k].get("ruleGroup"),
                   "type": live_map[k].get("ruleType"),
                   "use_yn": live_map[k].get("useYn"),
                   "modified_at": live_map[k].get("updDt")} for k in added],
        "changed": changed,
        "deleted": [{"key": k, "title": b[k].get("ruleNm")} for k in deleted],
    }


def render(d: dict) -> str:
    c = d["counts"]
    out = ["TS_INS_AI_RULES DIFF", f"baseline: {d['baseline']}", ""]
    out.append(f"ADDED     {c['added']:>4}")
    out.append(f"CHANGED   {c['changed']:>4}")
    out.append(f"DELETED   {c['deleted']:>4}")
    out.append(f"UNCHANGED {c['unchanged']:>4}")

    thr = [x for x in d["changed"] if x["threshold"]]
    if thr:
        out += ["", f"  ★ 그중 임계값(숫자) 변화: {len(thr)}건 — PigOS 검토 최우선"]

    if d["added"]:
        out += ["", "[ADDED]"]
        for x in d["added"]:
            out.append(f"  {x['key']}  |  {x['title']}  |  {x['category']}/{x['type']}"
                       f"  |  use={x['use_yn']}  |  {x['modified_at']}")
    if d["changed"]:
        out += ["", "[CHANGED]"]
        for x in d["changed"]:
            tag = "[THRESHOLD] " if x["threshold"] else ""
            out.append(f"  {tag}{x['key']}  |  {','.join(x['changed_fields'])}"
                       f"  |  {x['old_hash']} → {x['new_hash']}  |  {x['modified_at']}")
    if d["deleted"]:
        out += ["", "[DELETED]"]
        for x in d["deleted"]:
            out.append(f"  {x['key']}  |  {x['title']}")

    out += ["", "※ 관측 전용 — 자동 반영·seed·스냅샷 갱신을 하지 않는다.",
            "  변경을 PigOS 에 넣을지는 사람이 본문을 읽고 판단한다(위조 0)."]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="PigPlan 룰 diff (관측 전용)")
    ap.add_argument("--json", metavar="PATH", help="결과를 JSON 으로도 저장")
    ap.add_argument("--live", metavar="PATH",
                    help="Oracle 대신 이 JSON 파일을 라이브로 취급(테스트·오프라인용)")
    args = ap.parse_args()

    _load_dotenv()
    base = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    live = (json.loads(Path(args.live).read_text(encoding="utf-8"))
            if args.live else _fetch_live())
    if live is None:
        print("\n라이브 조회를 못 했습니다. **개발은 그대로 진행하십시오** — "
              "이 스크립트는 관측 장치이지 의존성이 아닙니다.", file=sys.stderr)
        return 2

    d = diff(base, live)
    print(render(d))
    if args.json:
        Path(args.json).write_text(json.dumps(d, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
        print(f"\nJSON 저장: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
