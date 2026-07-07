"""입력검증 UAT — 이상 데이터 거부/정상 데이터 수락을 CREATE·UPDATE·DELETE 전반에서 체계 검증.
토큰 1개 재사용(하니스 로그인 충돌 회피). CREATE는 dry_run 무오염. UPDATE/DELETE는 전용 테스트
모돈 라이프사이클로 격리 후 정리. 사용: python scripts/uat_validation.py
"""
import json, uuid, urllib.request, urllib.error, sys

BASE = "http://127.0.0.1:8000/api/v1"
FARM = "5ee6b97d-81c4-47bb-a4d9-e70a2ee1f96b"
EMAIL, PW = "test001@pigos.io", "123123"

def http(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token: req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try: detail = json.loads(raw)
        except Exception: detail = raw[:120]
        return e.code, detail

def U(): return str(uuid.uuid4())
def cca(d): return f"{d}T00:00:00Z"

def sync(token, changes, dry=True):
    body = {"client_id": U(), "dry_run": dry, "farm_id": FARM, "last_sync_at": None, "changes": changes}
    st, d = http("POST", f"/farms/{FARM}/sync", body, token)
    if st != 200: return f"HTTP{st}", d
    acc = len(d.get("accepted", []))
    rej = [r.get("reason") for r in d.get("rejected", [])]
    return ("ACCEPTED" if acc and not rej else "REJECTED"), rej

PASS, FAIL = "PASS", "FAIL"
results = []
def check(layer, name, got_blocked, expect_blocked, detail=""):
    ok = (got_blocked == expect_blocked)
    results.append((layer, PASS if ok else FAIL, name, f"{'거부' if got_blocked else '수락'} (기대:{'거부' if expect_blocked else '수락'}) {detail}"))

def main():
    global FARM
    # username 인증 전환(2026-06) + 격리농장 온보딩 — 하드코딩 farm/email 로그인 폐기.
    sfx = uuid.uuid4().hex[:6]
    st, d = http("POST", "/onboarding/complete", {
        "org_name": f"UAT {sfx}", "country": "KR", "name": "UAT",
        "username": f"uat_{sfx}", "email": f"uat_{sfx}@pigos.io",
        "password": "password1", "farm_name": f"UATF {sfx}"})
    token = d.get("access_token") if isinstance(d, dict) else None
    if st not in (200, 201) or not token:
        print(f"온보딩 실패 {st} {str(d)[:120]}"); sys.exit(1)
    FARM = d["farm_id"]
    # 상태별 모돈은 인자로 받음(psql로 미리 조회해 전달)
    OPEN = sys.argv[1] if len(sys.argv) > 1 else ""
    PREG = sys.argv[2] if len(sys.argv) > 2 else ""
    LAC = sys.argv[3] if len(sys.argv) > 3 else ""

    # ───── CREATE (dry_run 무오염) ─────
    # 분만: PREG 모돈에 정상 → 수락 기대
    if PREG:
        s, r = sync(token, {"farrowings": [{"id": U(), "sow_id": PREG, "farrowing_date": "2026-06-20", "total_born": 12, "born_alive": 11, "born_dead": 1, "mummies": 0, "client_created_at": cca("2026-06-20")}]})
        check("CREATE", "분만 정상(TB=11+1)", s != "ACCEPTED", False, str(r))
        # TB 산술 불일치(B1)
        s, r = sync(token, {"farrowings": [{"id": U(), "sow_id": PREG, "farrowing_date": "2026-06-20", "total_born": 20, "born_alive": 10, "born_dead": 0, "mummies": 0, "client_created_at": cca("2026-06-20")}]})
        check("CREATE", "분만 TB산술불일치(20≠10)", s == "REJECTED", True, str(r))
        # 미래일
        s, r = sync(token, {"farrowings": [{"id": U(), "sow_id": PREG, "farrowing_date": "2099-01-01", "total_born": 12, "born_alive": 11, "born_dead": 1, "mummies": 0, "client_created_at": cca("2099-01-01")}]})
        check("CREATE", "분만 미래일(2099)", s == "REJECTED", True, str(r))
        # total_born 과다(>35)
        s, r = sync(token, {"farrowings": [{"id": U(), "sow_id": PREG, "farrowing_date": "2026-06-20", "total_born": 99, "born_alive": 99, "born_dead": 0, "mummies": 0, "client_created_at": cca("2026-06-20")}]})
        check("CREATE", "분만 TB과다(99)", s == "REJECTED", True, str(r))
        # 음수
        s, r = sync(token, {"farrowings": [{"id": U(), "sow_id": PREG, "farrowing_date": "2026-06-20", "total_born": 5, "born_alive": -3, "born_dead": 8, "mummies": 0, "client_created_at": cca("2026-06-20")}]})
        check("CREATE", "분만 음수(BA=-3)", s == "REJECTED", True, str(r))
        # 날짜역순(분만 < 교배)
        s, r = sync(token, {"farrowings": [{"id": U(), "sow_id": PREG, "farrowing_date": "2020-01-01", "total_born": 12, "born_alive": 11, "born_dead": 1, "mummies": 0, "client_created_at": cca("2020-01-01")}]})
        check("CREATE", "분만 날짜역순(2020<교배)", s == "REJECTED", True, str(r))
    # 교배: PREG 모돈 재교배 → STATUS_CONFLICT 기대
    if PREG:
        s, r = sync(token, {"matings": [{"id": U(), "sow_id": PREG, "mating_date": "2026-06-10", "mating_type": "AI", "mating_number": 1, "client_created_at": cca("2026-06-10")}]})
        check("CREATE", "교배 PREGNANT재교배", s == "REJECTED", True, str(r))
    # 교배: 존재하지 않는 sow
    s, r = sync(token, {"matings": [{"id": U(), "sow_id": U(), "mating_date": "2026-06-10", "mating_type": "AI", "mating_number": 1, "client_created_at": cca("2026-06-10")}]})
    check("CREATE", "교배 없는모돈(SOW_NOT_FOUND)", s == "REJECTED", True, str(r))
    # 이유: LAC 모돈 정상 → 수락
    if LAC:
        s, r = sync(token, {"weanings": [{"id": U(), "sow_id": LAC, "weaning_date": "2026-06-21", "weaned_count": 10, "client_created_at": cca("2026-06-21")}]})
        check("CREATE", "이유 정상(10)", s != "ACCEPTED", False, str(r))
        # weaned 과다(>30)
        s, r = sync(token, {"weanings": [{"id": U(), "sow_id": LAC, "weaning_date": "2026-06-21", "weaned_count": 99, "client_created_at": cca("2026-06-21")}]})
        check("CREATE", "이유 과다(99)", s == "REJECTED", True, str(r))
        # weaned 음수
        s, r = sync(token, {"weanings": [{"id": U(), "sow_id": LAC, "weaning_date": "2026-06-21", "weaned_count": -5, "client_created_at": cca("2026-06-21")}]})
        check("CREATE", "이유 음수(-5)", s == "REJECTED", True, str(r))

    # ───── 전용 테스트 모돈 라이프사이클(UPDATE/DELETE용, 실제 영속 후 정리) ─────
    tag = "ZUAT-" + U()[:6]
    st, sow = http("POST", f"/farms/{FARM}/sows", {"ear_tag": tag, "entry_type": "GILT", "entry_date": "2025-06-01", "parity": 0}, token)
    sid = sow.get("id") if isinstance(sow, dict) else None
    if sid:
        # 정상 라이프사이클 영속(dry=False)
        mid_local = U(); fid_local = U(); wid_local = U()
        sync(token, {"matings": [{"id": mid_local, "sow_id": sid, "mating_date": "2026-01-10", "mating_type": "AI", "mating_number": 1, "client_created_at": cca("2026-01-10")}]}, dry=False)
        sync(token, {"farrowings": [{"id": fid_local, "sow_id": sid, "farrowing_date": "2026-05-05", "total_born": 12, "born_alive": 11, "born_dead": 1, "mummies": 0, "client_created_at": cca("2026-05-05")}]}, dry=False)
        sync(token, {"weanings": [{"id": wid_local, "sow_id": sid, "weaning_date": "2026-05-26", "weaned_count": 10, "client_created_at": cca("2026-05-26")}]}, dry=False)
        # 실제 영속된 이벤트 id 조회(서버 생성 id일 수 있음)
        st, fs = http("GET", f"/farms/{FARM}/events/farrowings?sow_id={sid}", token=token)
        real_fid = fs[0]["id"] if isinstance(fs, list) and fs else fid_local
        st, ws = http("GET", f"/farms/{FARM}/events/weanings?sow_id={sid}", token=token)
        real_wid = ws[0]["id"] if isinstance(ws, list) and ws else wid_local
        st, ms = http("GET", f"/farms/{FARM}/events/matings?sow_id={sid}", token=token)
        real_mid = ms[0]["id"] if isinstance(ms, list) and ms else mid_local

        # ───── UPDATE (수정) ─────
        # 정상 수정(notes) → 수락
        st, r = http("PATCH", f"/farms/{FARM}/events/farrowings/{real_fid}", {"notes": "uat-edit"}, token)
        check("UPDATE", "분만 notes수정", st >= 400, False, f"HTTP{st}")
        # TB 불일치 수정 → 서버가 total_born=born+sb+mm으로 자동유도(INV1 유지). 수락+보정(20→10) 검증.
        st, r = http("PATCH", f"/farms/{FARM}/events/farrowings/{real_fid}", {"total_born": 20, "born_alive": 10, "stillborn": 0, "mummified": 0}, token)
        derived_ok = st == 200 and isinstance(r, dict) and r.get("total_born") == 10
        check("UPDATE", "분만 TB불일치→자동유도(20→10)", not derived_ok, False, f"HTTP{st} tb={r.get('total_born') if isinstance(r, dict) else '?'}")
        # born_alive 음수 수정
        st, r = http("PATCH", f"/farms/{FARM}/events/farrowings/{real_fid}", {"born_alive": -5}, token)
        check("UPDATE", "분만 음수수정(BA=-5)", st >= 400, True, f"HTTP{st}")
        # 미래일 수정
        st, r = http("PATCH", f"/farms/{FARM}/events/farrowings/{real_fid}", {"farrowing_date": "2099-01-01"}, token)
        check("UPDATE", "분만 미래일수정(2099)", st >= 400, True, f"HTTP{st}")
        # 이유두수 과다 수정
        st, r = http("PATCH", f"/farms/{FARM}/events/weanings/{real_wid}", {"weaned_count": 99}, token)
        check("UPDATE", "이유 과다수정(99)", st >= 400, True, f"HTTP{st}")
        # 교배일 수정(P2: 500 회귀 확인)
        st, r = http("PATCH", f"/farms/{FARM}/events/matings/{real_mid}", {"mating_date": "2026-01-08"}, token)
        check("UPDATE", "교배일 수정(P2 500여부)", st >= 400, False, f"HTTP{st} {'<-500이면 P2버그' if st==500 else ''}")

        # ───── DELETE (삭제) 조건 ─────
        # 분만(이유 존재) 삭제 시도 → 차단 기대(409)
        st, r = http("DELETE", f"/farms/{FARM}/events/farrowings/{real_fid}", token=token)
        check("DELETE", "분만 삭제(이유 종속 존재)", st >= 400, True, f"HTTP{st}")
        # 이유(말단) 삭제 → 허용 기대
        st, r = http("DELETE", f"/farms/{FARM}/events/weanings/{real_wid}", token=token)
        check("DELETE", "이유 삭제(말단)", st >= 400, False, f"HTTP{st}")
        # 이유 삭제 후 분만 삭제 → 이제 허용?
        st, r = http("DELETE", f"/farms/{FARM}/events/farrowings/{real_fid}", token=token)
        check("DELETE", "분만 삭제(이유 제거 후)", st >= 400, False, f"HTTP{st}")
        # 정리: 테스트 모돈 삭제(잔여 캐스케이드)
        dc, _ = http("DELETE", f"/farms/{FARM}/sows/{sid}", token=token)
        results.append(("CLEANUP", "INFO", f"테스트모돈 {tag} 삭제", f"HTTP{dc}"))

    # ───── 번식이벤트(reproductive) CREATE via /sync dry_run ─────
    anysow = PREG or LAC
    if anysow:
        s, r = sync(token, {"reproductive_events": [{"id": U(), "sow_id": anysow, "event_type": "HEAT_DETECTED", "event_date": "2026-06-15", "client_created_at": cca("2026-06-15")}]})
        check("REPRO", "번식이벤트 정상(HEAT_DETECTED)", s != "ACCEPTED", False, str(r))
        s, r = sync(token, {"reproductive_events": [{"id": U(), "sow_id": anysow, "event_type": "BOGUS_TYPE", "event_date": "2026-06-15", "client_created_at": cca("2026-06-15")}]})
        check("REPRO", "번식이벤트 잘못된타입", s == "REJECTED", True, str(r))
        s, r = sync(token, {"reproductive_events": [{"id": U(), "sow_id": anysow, "event_type": "HEAT_DETECTED", "event_date": "2099-01-01", "client_created_at": cca("2099-01-01")}]})
        check("REPRO", "번식이벤트 미래일", s == "REJECTED", True, str(r))
    s, r = sync(token, {"reproductive_events": [{"id": U(), "sow_id": U(), "event_type": "HEAT_DETECTED", "event_date": "2026-06-15", "client_created_at": cca("2026-06-15")}]})
    check("REPRO", "번식이벤트 없는모돈", s == "REJECTED", True, str(r))

    # ───── 자돈이벤트(piglet) CREATE via /sync dry_run ─────
    if LAC:
        s, r = sync(token, {"piglet_events": [{"id": U(), "sow_id": LAC, "event_type": "DEATH", "event_date": "2026-06-20", "piglet_count": 1, "client_created_at": cca("2026-06-20")}]})
        check("PIGLET", "자돈폐사 정상(1두)", s != "ACCEPTED", False, str(r))
        s, r = sync(token, {"piglet_events": [{"id": U(), "sow_id": LAC, "event_type": "DEATH", "event_date": "2026-06-20", "piglet_count": 0, "client_created_at": cca("2026-06-20")}]})
        check("PIGLET", "자돈폐사 0두(piglet_count<1)", s == "REJECTED", True, str(r))
        s, r = sync(token, {"piglet_events": [{"id": U(), "sow_id": LAC, "event_type": "DEATH", "event_date": "2026-06-20", "piglet_count": -3, "client_created_at": cca("2026-06-20")}]})
        check("PIGLET", "자돈폐사 음수(-3)", s == "REJECTED", True, str(r))
        s, r = sync(token, {"piglet_events": [{"id": U(), "sow_id": LAC, "event_type": "ZZZ", "event_date": "2026-06-20", "piglet_count": 1, "client_created_at": cca("2026-06-20")}]})
        check("PIGLET", "자돈이벤트 잘못된타입", s == "REJECTED", True, str(r))

    # ───── 웅돈(boar) CRUD ─────
    btag = "ZUATB-" + U()[:6]
    st, b = http("POST", f"/farms/{FARM}/boars", {"ear_tag": btag, "breed": "Duroc", "entry_date": "2025-01-01", "entry_type": "PURCHASE"}, token)
    check("BOAR", "웅돈 정상등록", st >= 400, False, f"HTTP{st}")
    bid = b.get("id") if isinstance(b, dict) else None
    st, _ = http("POST", f"/farms/{FARM}/boars", {"ear_tag": btag, "breed": "Duroc", "entry_date": "2025-01-01", "entry_type": "PURCHASE"}, token)
    check("BOAR", "웅돈 중복이표", st >= 400, True, f"HTTP{st}")
    st, _ = http("POST", f"/farms/{FARM}/boars", {"ear_tag": "", "breed": "Duroc", "entry_date": "2025-01-01", "entry_type": "PURCHASE"}, token)
    check("BOAR", "웅돈 빈이표", st >= 400, True, f"HTTP{st}")
    st, _ = http("POST", f"/farms/{FARM}/boars", {"ear_tag": "ZUATB-future", "breed": "Duroc", "entry_date": "2099-01-01", "entry_type": "PURCHASE"}, token)
    check("BOAR", "웅돈 미래 입식일", st >= 400, True, f"HTTP{st}")
    if bid:
        st, _ = http("PATCH", f"/farms/{FARM}/boars/{bid}", {"status": "CULLED"}, token)
        check("BOAR", "웅돈 상태수정(CULL)", st >= 400, False, f"HTTP{st}")

    # ───── 비육돈(finisher) CRUD ─────
    st, g = http("POST", f"/farms/{FARM}/finishers", {"group_code": "ZUATF-" + U()[:5], "start_date": "2025-01-01", "head_count_in": 20}, token)
    check("FINISH", "비육 정상등록(20두)", st >= 400, False, f"HTTP{st}")
    gid = g.get("id") if isinstance(g, dict) else None
    st, _ = http("POST", f"/farms/{FARM}/finishers", {"group_code": "ZUATF-neg", "start_date": "2025-01-01", "head_count_in": -5}, token)
    check("FINISH", "비육 음수입식(-5)", st >= 400, True, f"HTTP{st}")
    if gid:
        st, _ = http("POST", f"/farms/{FARM}/finishers/{gid}/ship", {"end_date": "2025-06-01", "head_count_out": 50}, token)
        check("FINISH", "비육 출하>입식(50>20)", st >= 400, True, f"HTTP{st} (B5)")
        st, _ = http("DELETE", f"/farms/{FARM}/finishers/{gid}", token=token)

    # ───── 도폐사(cull) CRUD — 전용 모돈 ─────
    ctag = "ZUATC-" + U()[:6]
    st, csow = http("POST", f"/farms/{FARM}/sows", {"ear_tag": ctag, "entry_type": "GILT", "entry_date": "2025-06-01", "parity": 0}, token)
    csid = csow.get("id") if isinstance(csow, dict) else None
    if csid:
        st, _ = http("POST", f"/farms/{FARM}/sows/{csid}/cull", {"removal_type": "CULLED", "removal_date": "2099-01-01", "reason_category": "AGE"}, token)
        check("CULL", "도폐사 미래일(2099)", st >= 400, True, f"HTTP{st}")
        st, _ = http("POST", f"/farms/{FARM}/sows/{csid}/cull", {"removal_type": "CULLED", "removal_date": "2020-01-01", "reason_category": "AGE"}, token)
        check("CULL", "도폐사 입식일이전(2020<2025)", st >= 400, True, f"HTTP{st}")
        st, _ = http("POST", f"/farms/{FARM}/sows/{csid}/cull", {"removal_type": "CULLED", "removal_date": "2026-06-01", "reason_category": "AGE"}, token)
        check("CULL", "도폐사 정상", st >= 400, False, f"HTTP{st}")
        # 도폐사 후 교배 시도 → SOW_NOT_FOUND 기대
        s, r = sync(token, {"matings": [{"id": U(), "sow_id": csid, "mating_date": "2026-06-10", "mating_type": "AI", "mating_number": 1, "client_created_at": cca("2026-06-10")}]})
        check("CULL", "도폐사후 교배차단", s == "REJECTED", True, str(r))
        http("DELETE", f"/farms/{FARM}/sows/{csid}", token=token)

    # 출력
    print(f"\n{'='*70}\n입력검증 UAT 결과 (CREATE dry_run + UPDATE/DELETE 격리)\n{'='*70}")
    for layer, verdict, name, detail in results:
        print(f"  [{layer}] {verdict}  {name}: {detail}")
    npass = sum(1 for r in results if r[1] == PASS)
    print(f"\n  {npass}/{len(results)} PASS")

if __name__ == "__main__":
    main()
