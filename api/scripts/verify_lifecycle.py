"""라이브 /sync 라이프사이클 재검증 (B-1 수정 확인 + 이벤트 전종류).
login(test001) → 새 sow → 교배(1st sync) → 분만(2nd) → 이유(3rd). 각 반복 sync가 200/accepted인지.
실행: scripts/verify_lifecycle.py  (백엔드 떠 있어야 함)
"""
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
    st, login = call("POST", "/auth/login", body={"email": "test001@pigos.io", "password": "123123"})
    print(f"login: {st}")
    tok = login["access_token"]
    farm = login["farm_ids"][0]
    now = datetime.now(UTC).isoformat()

    st, sow = call("POST", f"/farms/{farm}/sows", tok,
                   {"ear_tag": f"LIFE-{uuid.uuid4().hex[:6]}", "entry_date": "2026-06-16", "entry_type": "GILT", "parity": 0})
    print(f"POST /sows: {st}  status={sow.get('status')}")
    sid = sow["id"]

    def sync(label, last, changes):
        body = {"farm_id": farm, "client_id": str(uuid.uuid4()), "last_sync_at": last, "dry_run": False, "changes": changes}
        st, r = call("POST", f"/farms/{farm}/sync", tok, body)
        if isinstance(r, dict):
            acc = [f"{a['entity']}/{a['action']}" for a in r.get("accepted", [])]
            rej = [x["reason"] for x in r.get("rejected", [])]
            print(f"{label}: HTTP {st}  accepted={acc} rejected={rej} pulled={r.get('stats',{}).get('pulled')}")
            return r.get("sync_token")
        print(f"{label}: HTTP {st}  {r}")
        return None

    t1 = sync("① 교배(1st)", None,
              {"matings": [{"id": str(uuid.uuid4()), "sow_id": sid, "mating_date": "2026-06-16", "mating_type": "AI", "mating_number": 1, "client_created_at": now}]})
    t2 = sync("② 분만(2nd, B-1)", t1,
              {"farrowings": [{"id": str(uuid.uuid4()), "sow_id": sid, "farrowing_date": "2026-06-16", "total_born": 12, "born_alive": 11, "born_dead": 1, "mummies": 0, "farrowing_type": "NORMAL", "client_created_at": now}]})
    t3 = sync("③ 이유(3rd)", t2,
              {"weanings": [{"id": str(uuid.uuid4()), "sow_id": sid, "weaning_date": "2026-06-16", "weaned_count": 10, "avg_weight_kg": 6.5, "client_created_at": now}]})
    sync("④ 포유자돈폐사(4th)", t3,
         {"piglet_events": [{"id": str(uuid.uuid4()), "sow_id": sid, "event_date": "2026-06-16", "event_type": "DEATH", "piglet_count": 1, "reason": "CRUSHING", "client_created_at": now}]})


if __name__ == "__main__":
    main()
