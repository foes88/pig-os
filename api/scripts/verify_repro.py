"""reproductive_events(도폐사/임신사고) 라이브 검증 + 상태전이 확인."""
import json
import urllib.request
import uuid
from datetime import UTC, datetime

B = "http://127.0.0.1:8000/api/v1"


def call(method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(B + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]


def main():
    _, login = call("POST", "/auth/login", body={"email": "test001@pigos.io", "password": "123123"})
    tok = login["access_token"]
    farm = login["farm_ids"][0]
    now = datetime.now(UTC).isoformat()

    def new_sow():
        _, s = call("POST", f"/farms/{farm}/sows", tok,
                    {"ear_tag": f"REP-{uuid.uuid4().hex[:6]}", "entry_date": "2026-06-16", "entry_type": "GILT", "parity": 0})
        return s["id"]

    def sync(label, last, changes):
        body = {"farm_id": farm, "client_id": str(uuid.uuid4()), "last_sync_at": last, "dry_run": False, "changes": changes}
        st, r = call("POST", f"/farms/{farm}/sync", tok, body)
        acc = [f"{a['entity']}/{a['action']}" for a in r.get("accepted", [])] if isinstance(r, dict) else r
        rej = [x["reason"] for x in r.get("rejected", [])] if isinstance(r, dict) else ""
        print(f"{label}: HTTP {st} accepted={acc} rejected={rej}")
        return r.get("sync_token") if isinstance(r, dict) else None

    def status(sid):
        _, s = call("GET", f"/sows/{sid}", tok)
        return s.get("status") if isinstance(s, dict) else s

    # 도폐사: GILT sow → CULLED reproductive event
    s1 = new_sow()
    t = sync("도폐사 CULLED", None,
             {"reproductive_events": [{"id": str(uuid.uuid4()), "sow_id": s1, "event_type": "CULLED", "event_date": "2026-06-16", "client_created_at": now}]})
    print(f"   sow status → {status(s1)} (기대 CULLED)")

    # 임신사고: 교배(PREGNANT) → ABORTION
    s2 = new_sow()
    t = sync("교배", None, {"matings": [{"id": str(uuid.uuid4()), "sow_id": s2, "mating_date": "2026-06-16", "mating_type": "AI", "mating_number": 1, "client_created_at": now}]})
    sync("임신사고 ABORTION (2nd)", t,
         {"reproductive_events": [{"id": str(uuid.uuid4()), "sow_id": s2, "event_type": "ABORTION", "event_date": "2026-06-16", "client_created_at": now}]})
    print(f"   sow status → {status(s2)}")


if __name__ == "__main__":
    main()
