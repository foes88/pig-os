"""B4 정공법 라이브 검증 — 처리순서 재정렬 + 유효복당 검증.

각 시나리오: GILT 모돈 생성 → 한 /sync 배치 [mating, farrowing, piglet_events, weaning]
(non-dry_run, 실영속) → weaning 수락/거부 확인 → 모돈 삭제(정리).

핵심:
  A 정상(no foster): farrow12, wean10 → accepted
  B 과잉이유: farrow10, wean15 → REJECTED (유효복당 10 초과)
  C 폐사 반영: farrow12, DEATH5, wean8 → REJECTED (유효 7, 8>7) ← 폐사가 이유보다 먼저 처리돼야
  D nurse sow: farrow10, FOSTER_IN5, wean14 → accepted (유효 15) ← 양자가 이유보다 먼저 처리돼야(오거부 X)
  E 부분이유: farrow12, wean7 then wean5 → 둘 다 accepted(합12=유효), 추가 wean1 → REJECTED(잔여0)
"""
import json
import urllib.request
import urllib.error
import uuid

BASE = "http://127.0.0.1:8000/api/v1"
FARM = "5ee6b97d-81c4-47bb-a4d9-e70a2ee1f96b"


def http(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw[:200]


def U():
    return str(uuid.uuid4())


def cca(d):
    return f"{d}T00:00:00Z"


def login():
    _, d = http("POST", "/auth/login", {"email": "test001@pigos.io", "password": "123123"})
    return d["access_token"]


def new_sow(token, tag):
    st, s = http("POST", f"/farms/{FARM}/sows",
                 {"ear_tag": tag, "entry_type": "GILT", "entry_date": "2025-06-01", "parity": 0}, token)
    return s.get("id") if isinstance(s, dict) else None


def sync_batch(token, changes):
    body = {"client_id": U(), "dry_run": False, "farm_id": FARM, "last_sync_at": None, "changes": changes}
    st, d = http("POST", f"/farms/{FARM}/sync", body, token)
    return d


def weaning_result(d):
    acc = d.get("accepted", [])
    rej = d.get("rejected", [])
    w_acc = any(a.get("entity") == "weaning" for a in acc)
    w_rej = [r for r in rej if r.get("entity") == "weaning"]
    if w_rej:
        return "REJECTED", w_rej[0].get("reason"), w_rej[0].get("detail", {}).get("message", "")
    if w_acc:
        return "ACCEPTED", None, ""
    return "NO_WEANING", None, ""


def main():
    token = login()
    results = []

    def run(name, sow_tag, events, expect):
        sid = new_sow(token, sow_tag)
        if not sid:
            results.append((name, "SETUP_FAIL", expect, ""))
            return
        # mating + farrowing 공통
        ch = {
            "matings": [{"id": U(), "sow_id": sid, "mating_date": "2026-01-10", "mating_type": "AI",
                         "mating_number": 1, "client_created_at": cca("2026-01-10")}],
            "farrowings": [dict(id=U(), sow_id=sid, farrowing_date="2026-05-05",
                                client_created_at=cca("2026-05-05"), **events["farrowing"])],
        }
        if events.get("piglet_events"):
            ch["piglet_events"] = [dict(id=U(), sow_id=sid, client_created_at=cca("2026-05-15"), **pe)
                                   for pe in events["piglet_events"]]
        ch["weanings"] = [dict(id=U(), sow_id=sid, weaning_date="2026-05-26",
                               client_created_at=cca("2026-05-26"), **w) for w in events["weanings"]]
        d = sync_batch(token, ch)
        status, reason, msg = weaning_result(d)
        ok = (status == expect)
        results.append((name, status, expect, f"{reason or ''} {msg}".strip()))
        http("DELETE", f"/farms/{FARM}/sows/{sid}", token=token)
        return ok

    # A 정상(no foster): farrow BA=12, wean 10
    run("A 정상 farrow12 wean10", "ZB4-A-" + U()[:6],
        {"farrowing": {"total_born": 12, "born_alive": 12, "born_dead": 0, "mummies": 0},
         "weanings": [{"weaned_count": 10}]}, "ACCEPTED")

    # B 과잉이유: farrow BA=10, wean 15
    run("B 과잉 farrow10 wean15", "ZB4-B-" + U()[:6],
        {"farrowing": {"total_born": 10, "born_alive": 10, "born_dead": 0, "mummies": 0},
         "weanings": [{"weaned_count": 15}]}, "REJECTED")

    # C 폐사 반영: farrow BA=12, DEATH 5 → 유효 7, wean 8 → REJECTED (폐사가 먼저 처리돼야)
    run("C 폐사 farrow12 death5 wean8", "ZB4-C-" + U()[:6],
        {"farrowing": {"total_born": 12, "born_alive": 12, "born_dead": 0, "mummies": 0},
         "piglet_events": [{"event_type": "DEATH", "event_date": "2026-05-15", "piglet_count": 5, "reason": "CRUSHING"}],
         "weanings": [{"weaned_count": 8}]}, "REJECTED")

    # D nurse sow: farrow BA=10, FOSTER_IN 5 → 유효 15, wean 14 → ACCEPTED (양자가 먼저 처리돼 오거부 X)
    run("D nurse farrow10 fosterin5 wean14", "ZB4-D-" + U()[:6],
        {"farrowing": {"total_born": 10, "born_alive": 10, "born_dead": 0, "mummies": 0},
         "piglet_events": [{"event_type": "FOSTER_IN", "event_date": "2026-05-15", "piglet_count": 5}],
         "weanings": [{"weaned_count": 14}]}, "ACCEPTED")

    print(f"\n{'='*72}\nB4 정공법 라이브 검증 (처리순서 재정렬 + 유효복당)\n{'='*72}")
    npass = 0
    for name, got, exp, detail in results:
        ok = got == exp
        npass += ok
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {got} (기대 {exp}) {detail[:60]}")
    print(f"\n  {npass}/{len(results)} PASS")


if __name__ == "__main__":
    main()
