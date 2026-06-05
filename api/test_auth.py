import json, urllib.request, urllib.error

BASE = "http://localhost:8000/api/v1/auth"

def post(path, body):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

status, data = post("/login", {"email": "httptest2@pigos.io", "password": "Test1234!"})
print(f"1. Login {status}", "OK" if status == 200 else "FAIL")
refresh = data["refresh_token"]

status, data2 = post("/refresh", {"refresh_token": refresh})
print(f"2. Refresh {status}", "OK" if status == 200 else f"FAIL: {data2}")
new_refresh = data2.get("refresh_token", "")

status, _ = post("/logout", {"refresh_token": new_refresh})
print(f"3. Logout {status}", "OK" if status == 204 else f"GOT {status}")

status, data3 = post("/refresh", {"refresh_token": refresh})
print(f"4. Revoked token {status}", "OK (rejected)" if status == 401 else f"WRONG - {status}")

print("\n=== auth 검증 완료 ===")
