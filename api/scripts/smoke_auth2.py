import json
import urllib.error
import urllib.request

BASE = "http://localhost:8000/api/v1/auth"

def post(path, body):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        print(f"  HTTP Error {e.code}: {raw[:200]}")
        return e.code, json.loads(raw) if raw else {}

status, data = post("/login", {"email": "httptest2@pigos.io", "password": "Test1234!"})
print(f"1. Login {status}", "OK" if status == 200 else f"FAIL data={data}")
