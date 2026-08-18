"""PigPlan → PigOS 하베스트 임포터 (Stage 2/3).

READ-ONLY로 PigPlan Oracle에서 추출 → PigOS Postgres에 적재.
- 멱등성: 소스키 기반 결정론 uuid5 PK + ON CONFLICT DO NOTHING (스키마 변경 불필요).
- 사이클 재구성: 모돈별 시간순 상태머신 (교배 G → 분만 B → 이유 E). FK NOT NULL 체인 충족.
- PII 제외: 농장/농장주 실명 미추출. 합성 신원은 manifest에서만.
- 신원/분류: data_origin='pigplan_migration', data_classification='internal_reference', kpi_convention_origin=KR.

사용:
  uv run --with oracledb python scripts/harvest_import.py --bootstrap --farm 4372
  uv run --with oracledb python scripts/harvest_import.py --all
환경:
  ORACLE_DSN/ORACLE_USER/ORACLE_PW (기본값 코드 상수), PG_DSN (기본 로컬 pigos)
"""
from __future__ import annotations

import argparse
import os
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timedelta


def _load_dotenv():
    """api/.env.harvest(gitignore됨)에서 하베스트 비밀값 로드 — 기존 os.environ 우선.
    앱의 pydantic Settings 는 api/.env(extra=forbid)만 읽으므로 여기 키를 섞지 않는다."""
    envp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.harvest")
    if not os.path.exists(envp):
        return
    with open(envp, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()

# ── 접속 (비밀값은 환경변수/gitignore된 api/.env 로만 — 코드 하드코딩 금지) ────
ORACLE_DSN = os.getenv("ORACLE_DSN", "pigclouddb.c8ks4denaq5l.ap-northeast-2.rds.amazonaws.com:1521/PIGPLAN")
ORACLE_USER = os.getenv("ORACLE_USER", "pksu")
ORACLE_PW = os.getenv("ORACLE_PW")  # 필수 — 미설정 시 종료
PG_DSN = os.getenv("PG_DSN", "dbname=pigos user=pigos password=pigos host=localhost port=5432")
PROD_PG_DSN = os.getenv("PROD_PG_DSN")  # --prod 용 (api/.env)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.harvest.manifest import ORGANIZATIONS, build_manifest  # noqa: E402

NS = uuid.uuid5(uuid.NAMESPACE_DNS, "pigos.harvest.pigplan")


def uid(*parts) -> uuid.UUID:
    return uuid.uuid5(NS, ":".join(str(p) for p in parts))


def parse_wk(s: str | None) -> datetime | None:
    """CHAR(8) YYYYMMDD → date. 불량값(범위밖/형식오류)은 None."""
    if not s or len(s) != 8 or not s.isdigit():
        return None
    y, m, d = int(s[:4]), int(s[4:6]), int(s[6:8])
    if not (1990 <= y <= 2027 and 1 <= m <= 12 and 1 <= d <= 31):
        return None
    try:
        return datetime(y, m, d)
    except ValueError:
        return None


# ── PigPlan 추출 (READ-ONLY) ─────────────────────────────────────────────────
def fetch_farm(cur, farm_no: int) -> dict:
    """모돈 + 이벤트 상세를 한 농장분 메모리로. PII 컬럼 미포함."""
    out: dict = {"sows": {}, "wk": defaultdict(list), "gyobae": {}, "bunman": {}, "eu": {}}
    cur.execute("""
        SELECT PIG_NO, FARM_PIG_NO, PUMJONG_CD, RFID_NO, BIRTH_DT, IN_DT, IN_SANCHA,
               OUT_DT, OUT_GUBUN_CD, HYULTONG_NO
        FROM TB_MODON WHERE FARM_NO=:f""", {"f": farm_no})
    for r in cur.fetchall():
        out["sows"][r[0]] = dict(pig_no=r[0], ear_tag=r[1], breed=r[2], rfid=r[3],
                                 birth=r[4], in_dt=r[5], in_sancha=r[6] or 0,
                                 out_dt=r[7], out_gubun=r[8], hyultong=r[9])
    cur.execute("SELECT PIG_NO, WK_DT, WK_GUBUN, SANCHA, GYOBAE_CNT FROM TB_MODON_WK WHERE FARM_NO=:f AND USE_YN='Y'", {"f": farm_no})
    for pig, wk, gub, sancha, gc in cur.fetchall():
        out["wk"][pig].append((wk, gub, sancha, gc or 0))
    cur.execute("SELECT PIG_NO, WK_DT, METHOD_1, UFARM_PIG_NO_1 FROM TB_GYOBAE WHERE FARM_NO=:f", {"f": farm_no})
    for pig, wk, meth, boar in cur.fetchall():
        out["gyobae"][(pig, wk)] = (meth, boar)
    cur.execute("SELECT PIG_NO, WK_DT, SILSAN, SASAN, MILA, SAENGSI_KG FROM TB_BUNMAN WHERE FARM_NO=:f", {"f": farm_no})
    for pig, wk, silsan, sasan, mila, kg in cur.fetchall():
        out["bunman"][(pig, wk)] = (silsan or 0, sasan or 0, mila or 0, kg)
    cur.execute("SELECT PIG_NO, WK_DT, DUSU, DUSU_SU, ILRYUNG, TOTAL_KG FROM TB_EU WHERE FARM_NO=:f", {"f": farm_no})
    for pig, wk, du, du_su, il, kg in cur.fetchall():
        out["eu"][(pig, wk)] = ((du or 0) + (du_su or 0), il, kg)
    return out


# ── 사이클 재구성 상태머신 ────────────────────────────────────────────────────
_GUBUN_ORDER = {"G": 0, "B": 1, "E": 2, "F": 3}


def reconstruct(pig_no, wk_events, src) -> tuple[list[dict], int, int]:
    """모돈 이벤트열 → 사이클 리스트. (cycles, orphan_far, orphan_wea)."""
    evs = []
    for wk, gub, sancha, gc in wk_events:
        d = parse_wk(wk)
        if d:
            evs.append((d, _GUBUN_ORDER.get(gub, 9), gub, wk, sancha, gc))
    evs.sort()
    cycles: list[dict] = []
    cur = None
    orphan_far = orphan_wea = 0
    for d, _, gub, wk, sancha, gc in evs:
        if gub == "G":
            det = src["gyobae"].get((pig_no, wk), (None, None))
            m = dict(date=d, wk=wk, gc=gc, method=det[0], boar=det[1])
            if cur is None or cur.get("farrowing"):
                cur = dict(sancha=sancha, matings=[m], farrowing=None, weaning=None, status="MATED")
                cycles.append(cur)
            else:
                cur["matings"].append(m)
        elif gub == "B":
            det = src["bunman"].get((pig_no, wk))
            if det is None:
                continue
            if cur and not cur["farrowing"]:
                cur["farrowing"] = dict(date=d, wk=wk, silsan=det[0], sasan=det[1], mila=det[2], kg=det[3])
                cur["status"] = "FARROWED"
            else:
                # orphan 분만(선행 교배 미매칭): PigPlan에 분만은 있으나 교배 레코드 누락/WK 미스매치가
                # ~9% → 통째로 버리면 PSY·모돈회전율·NPD가 일괄 과소/과대. 교배를 합성(임신 114일 역산)해
                # 사이클을 만들어 분만을 보존한다. 합성 교배는 wk="{wk}S"·method="SYNTH"로 식별 가능.
                synth = d - timedelta(days=114)
                cur = dict(sancha=sancha,
                           matings=[dict(date=synth, wk=f"{wk}S", gc=0, method="SYNTH", boar=None)],
                           farrowing=dict(date=d, wk=wk, silsan=det[0], sasan=det[1], mila=det[2], kg=det[3]),
                           weaning=None, status="FARROWED")
                cycles.append(cur)
                orphan_far += 1  # 이제 '합성 복구' 건수(추적용)
        elif gub == "E":
            det = src["eu"].get((pig_no, wk))
            if det is None:
                continue
            if cur and cur["farrowing"] and not cur["weaning"]:
                cur["weaning"] = dict(date=d, wk=wk, weaned=det[0], ilryung=det[1], kg=det[2])
                cur["status"] = "WEANED"
                cur = None
            else:
                orphan_wea += 1
        elif gub == "F":  # 재발/공태/유산 — 진행중 사이클(미분만) 실패 처리
            if cur and not cur["farrowing"]:
                cur["status"] = "FAILED"
                cur["repro"] = d
                cur = None
    return cycles, orphan_far, orphan_wea


# ── PigOS 행 생성 ────────────────────────────────────────────────────────────
def build_rows(farm_no, farm_id, src):
    """src → dict of table→list[tuple] for bulk insert."""
    R = dict(sows=[], cycles=[], matings=[], farrowings=[], weanings=[], repro=[])
    stats = dict(sows=0, cycles=0, matings=0, farrowings=0, weanings=0, orphan_far=0, orphan_wea=0)
    seen_tags: set[str] = set()  # ear_tag 재사용(개체번호 재할당) 결정론적 구분
    for pig_no in sorted(src["sows"].keys()):
        s = src["sows"][pig_no]
        sow_id = uid("sow", farm_no, pig_no)
        tag = (s["ear_tag"] or str(pig_no))[:30]
        if tag in seen_tags:
            tag = f"{tag[:20]}#{pig_no}"[:30]  # 후순위 재사용분에 시스템번호 접미
        seen_tags.add(tag)
        s = {**s, "ear_tag": tag}
        cycles, of, ow = reconstruct(pig_no, src["wk"].get(pig_no, []), src)
        stats["orphan_far"] += of
        stats["orphan_wea"] += ow
        # 활성 사이클은 모돈당 최대 1건(idx_one_active_cycle). 이유 미기록 후 재교배로
        # 중간에 남은 미완료 사이클(FARROWED/MATED)은 종결 처리(FAILED). 마지막만 활성 허용.
        # 분만 데이터(farrowing row)는 그대로 보존 — cycle_status만 종결.
        for c in cycles[:-1]:
            if c["status"] not in ("WEANED", "FAILED"):
                c["status"] = "FAILED"
        n_far = sum(1 for c in cycles if c["farrowing"])
        entry_type = "GILT" if (s["in_sancha"] or 0) <= 1 else "PURCHASE"
        # 현재 상태: 도폐사면 CULLED, 아니면 마지막 사이클 상태로 근사
        if s["out_dt"]:
            status = "CULLED"
        elif cycles:
            last = cycles[-1]
            status = {"MATED": "PREGNANT", "FARROWED": "LACTATING", "WEANED": "OPEN", "FAILED": "ACCIDENT"}[last["status"]]
        else:
            status = "GILT" if entry_type == "GILT" else "OPEN"
        entry_dt = s["in_dt"] or s["birth"] or datetime(2015, 1, 1)
        R["sows"].append((sow_id, farm_id, (s["ear_tag"] or str(pig_no))[:30], (s["rfid"] or None),
                          n_far, (s["breed"] or None), status, entry_dt, entry_type,
                          s["out_dt"], (s["hyultong"] or None), False, True))
        stats["sows"] += 1
        for idx, c in enumerate(cycles, start=1):
            cyc_id = uid("cyc", farm_no, pig_no, idx)
            first_m = c["matings"][0]
            # 종료일: 원본 이벤트일 기준(이관 시각 아님). WEANED=이유일, FAILED=재발/공태일.
            ended = (c["weaning"]["date"] if (c["status"] == "WEANED" and c["weaning"])
                     else c.get("repro") if c["status"] == "FAILED" else None)
            R["cycles"].append((cyc_id, farm_id, sow_id, idx, c["status"], first_m["date"],
                                len(c["matings"]), ended))
            stats["cycles"] += 1
            mat_ids = []
            for mn, m in enumerate(c["matings"], start=1):
                mid = uid("mat", farm_no, pig_no, m["wk"], m["gc"])
                mtype = "AI" if (m["method"] or "").upper().startswith("A") else "NATURAL"
                R["matings"].append((mid, farm_id, sow_id, cyc_id, m["date"].date(), mtype, mn))
                mat_ids.append(mid)
                stats["matings"] += 1
            if c["farrowing"]:
                f = c["farrowing"]
                fid = uid("far", farm_no, pig_no, f["wk"])
                tb = f["silsan"] + f["sasan"] + f["mila"]
                ba = f["silsan"]
                avg_bw = None
                if f["kg"] and ba > 0:
                    v = float(f["kg"]) / ba if float(f["kg"]) > ba else float(f["kg"])
                    avg_bw = round(min(v, 3.0), 3)
                R["farrowings"].append((fid, farm_id, sow_id, mat_ids[0], cyc_id, f["date"].date(),
                                        tb, ba, f["sasan"], f["mila"], ba, avg_bw))
                stats["farrowings"] += 1
                if c["weaning"]:
                    w = c["weaning"]
                    wid = uid("wea", farm_no, pig_no, w["wk"])
                    avg_ww = round(float(w["kg"]) / w["weaned"], 2) if (w["kg"] and w["weaned"]) else None
                    R["weanings"].append((wid, farm_id, sow_id, fid, cyc_id, w["date"].date(),
                                          w["weaned"], w["ilryung"], avg_ww))
                    stats["weanings"] += 1
    return R, stats


# ── Postgres 적재 ────────────────────────────────────────────────────────────
def upsert(pg, R):
    """적재. 사이클은 재이관 시 상태가 갱신돼야 하므로 DO UPDATE.

    반쪽 이관 사고(2026-07/08) 원인: 사이클을 ON CONFLICT (id) DO NOTHING 으로만 넣어
    이미 만든 사이클이 원본에서 닫혀도(이유 완료) PigOS 는 MATED/FARROWED 로 고착됐다.
    그 상태에서 다음 산차 사이클을 넣으려 하면 부분 유니크 인덱스
    idx_one_active_cycle (sow_id WHERE cycle_status NOT IN ('WEANED','FAILED')) 에 걸려
    UniqueViolation 으로 이관이 중단된다. (DO NOTHING 은 PK 충돌만 처리 — 부분 유니크는 못 막음)

    ★ 순서: 닫힌 사이클(WEANED/FAILED)을 **먼저** UPDATE 해 부분 유니크를 해제한 뒤,
      활성 사이클(MATED/FARROWED)을 넣는다. 이 순서가 아니면 같은 지점에서 다시 멈춘다.
    """
    import psycopg2.extras as ex
    cur = pg.cursor()

    def run(sql, rows):
        if rows:
            ex.execute_values(cur, sql, rows, page_size=1000)

    run("""INSERT INTO sows (id, farm_id, ear_tag, rfid_tag, parity, breed, status,
             entry_date, entry_type, exit_date, genetics_id, nurse_sow_flag, ractopamine_free) VALUES %s
           ON CONFLICT (id) DO NOTHING""", R["sows"])

    # 사이클: 상태·교배횟수·종료일 동기화. ended_at 은 원본 이벤트일(닫힘일 때만).
    cycle_sql = """INSERT INTO breeding_cycles
             (id, farm_id, sow_id, parity, cycle_status, started_at, mating_count, ended_at)
           VALUES %s
           ON CONFLICT (id) DO UPDATE SET
             cycle_status = EXCLUDED.cycle_status,
             mating_count = EXCLUDED.mating_count,
             ended_at     = EXCLUDED.ended_at,
             updated_at   = now()
           WHERE breeding_cycles.cycle_status IS DISTINCT FROM EXCLUDED.cycle_status
              OR breeding_cycles.mating_count IS DISTINCT FROM EXCLUDED.mating_count
              OR breeding_cycles.ended_at     IS DISTINCT FROM EXCLUDED.ended_at"""
    closed = [c for c in R["cycles"] if c[4] in ("WEANED", "FAILED")]
    active = [c for c in R["cycles"] if c[4] not in ("WEANED", "FAILED")]
    run(cycle_sql, closed)   # ★ 먼저 — 열린 사이클을 닫아 부분 유니크 해제
    run(cycle_sql, active)   # 그 다음 — 신규 활성 사이클 삽입

    # 교배도 원본 사후정정 실측(농장4448 11건) — 분만율의 분모라 정정 미반영 시 FR이 틀어진다.
    run("""INSERT INTO matings (id, farm_id, sow_id, breeding_cycle_id, mating_date, mating_type, mating_number)
           VALUES %s
           ON CONFLICT (id) DO UPDATE SET
             mating_date        = EXCLUDED.mating_date,
             mating_type        = EXCLUDED.mating_type,
             mating_number      = EXCLUDED.mating_number,
             breeding_cycle_id  = EXCLUDED.breeding_cycle_id,
             updated_at         = now()
           WHERE matings.mating_date       IS DISTINCT FROM EXCLUDED.mating_date
              OR matings.mating_type       IS DISTINCT FROM EXCLUDED.mating_type
              OR matings.mating_number     IS DISTINCT FROM EXCLUDED.mating_number
              OR matings.breeding_cycle_id IS DISTINCT FROM EXCLUDED.breeding_cycle_id""", R["matings"])

    # 분만/이유: 원본 사후정정(LOG_UPT_DT 갱신)이 실측되므로 실측치를 반영한다.
    run("""INSERT INTO farrowings (id, farm_id, sow_id, mating_id, breeding_cycle_id, farrowing_date,
             total_born, born_alive, stillborn, mummified, nursing_head, avg_birth_weight_kg)
           VALUES %s
           ON CONFLICT (id) DO UPDATE SET
             farrowing_date       = EXCLUDED.farrowing_date,
             total_born           = EXCLUDED.total_born,
             born_alive           = EXCLUDED.born_alive,
             stillborn            = EXCLUDED.stillborn,
             mummified            = EXCLUDED.mummified,
             nursing_head         = EXCLUDED.nursing_head,
             avg_birth_weight_kg  = EXCLUDED.avg_birth_weight_kg,
             updated_at           = now()
           WHERE farrowings.farrowing_date      IS DISTINCT FROM EXCLUDED.farrowing_date
              OR farrowings.total_born          IS DISTINCT FROM EXCLUDED.total_born
              OR farrowings.born_alive          IS DISTINCT FROM EXCLUDED.born_alive
              OR farrowings.stillborn           IS DISTINCT FROM EXCLUDED.stillborn
              OR farrowings.mummified           IS DISTINCT FROM EXCLUDED.mummified
              OR farrowings.nursing_head        IS DISTINCT FROM EXCLUDED.nursing_head
              OR farrowings.avg_birth_weight_kg IS DISTINCT FROM EXCLUDED.avg_birth_weight_kg""", R["farrowings"])
    run("""INSERT INTO weanings (id, farm_id, sow_id, farrowing_id, breeding_cycle_id, weaning_date,
             weaned_count, weaning_age_days, avg_weaning_weight_kg)
           VALUES %s
           ON CONFLICT (id) DO UPDATE SET
             weaning_date          = EXCLUDED.weaning_date,
             weaned_count          = EXCLUDED.weaned_count,
             weaning_age_days      = EXCLUDED.weaning_age_days,
             avg_weaning_weight_kg = EXCLUDED.avg_weaning_weight_kg,
             updated_at            = now()
           WHERE weanings.weaning_date          IS DISTINCT FROM EXCLUDED.weaning_date
              OR weanings.weaned_count          IS DISTINCT FROM EXCLUDED.weaned_count
              OR weanings.weaning_age_days      IS DISTINCT FROM EXCLUDED.weaning_age_days
              OR weanings.avg_weaning_weight_kg IS DISTINCT FROM EXCLUDED.avg_weaning_weight_kg""", R["weanings"])
    pg.commit()
    cur.close()


def ensure_farm(pg, mrow):
    """org + farm 행 보장 (합성 신원, PII 없음)."""
    cur = pg.cursor()
    fno = mrow["source_farm_ref"]
    cc = mrow["country_code"]
    org_id = None
    if mrow["organization_id"]:
        oid = mrow["organization_id"]
        org = ORGANIZATIONS[oid]
        org_id = uid("org", oid)
        cur.execute("""INSERT INTO organizations (id, name, org_type, org_level, country, timezone)
                       VALUES (%s,%s,%s,0,%s,'UTC') ON CONFLICT (id) DO NOTHING""",
                    (org_id, org["name"], "producer_group", cc))
    else:
        org_id = uid("org", "solo", fno)
        cur.execute("""INSERT INTO organizations (id, name, org_type, org_level, country, timezone)
                       VALUES (%s,%s,'independent',0,%s,'UTC') ON CONFLICT (id) DO NOTHING""",
                    (org_id, mrow["farm_name"], cc))
    farm_id = uid("farm", fno)
    cur.execute("""INSERT INTO farms (id, org_id, farm_code, name, country, region, timezone,
                     unit_system, language, currency, date_format, notification_channel,
                     farm_scale, internet_reliability, active, data_origin, data_classification)
                   VALUES (%s,%s,%s,%s,%s,%s,'UTC','METRIC','en','USD','yyyy-MM-dd','EMAIL',
                     'COMMERCIAL','HIGH',TRUE,'pigplan_migration','internal_reference')
                   ON CONFLICT (id) DO NOTHING""",
                (farm_id, org_id, f"PP-{fno}", mrow["farm_name"], cc, mrow["region"]))
    pg.commit()
    cur.close()
    return farm_id, org_id


# 데모 계정 공통 비밀번호(환경변수 우선). 내부 참조용 계정 — 운영 고객계정 아님.
DEMO_PW = os.getenv("HARVEST_DEMO_PW", "Harvest2026!")


def ensure_user(pg, farm_id, org_id, mrow, pw_hash):
    """농장별 FARM_OWNER 계정가입 + farm 멤버십. 합성 신원(오너명), PII 없음."""
    cur = pg.cursor()
    fno = mrow["source_farm_ref"]
    user_id = uid("user", fno)
    username = f"pp{fno}"
    email = f"pp-{fno}@harvest.pigos.io"
    cur.execute("""INSERT INTO users (id, org_id, username, email, name, password_hash,
                     role, system_role, language, active, approval_status)
                   VALUES (%s,%s,%s,%s,%s,%s,'FARM_OWNER','FARM_OWNER','en',TRUE,'APPROVED')
                   ON CONFLICT (id) DO NOTHING""",
                (user_id, org_id, username, email, mrow["owner_name"], pw_hash))
    cur.execute("""INSERT INTO user_farms (user_id, farm_id, role_override)
                   VALUES (%s,%s,'FARM_OWNER') ON CONFLICT (user_id, farm_id) DO NOTHING""",
                (user_id, farm_id))
    pg.commit()
    cur.close()
    return dict(farm=f"PP-{fno}", country=mrow["country_code"], username=username,
                email=email, password=DEMO_PW)


def bootstrap_schema():
    """빈 pigos DB에 현행 모델 스키마 + KPI 뷰/함수 생성 (create_all 기반)."""
    from sqlalchemy import create_engine

    import app.db.models  # noqa: F401 — 모든 모델 등록
    from app.db.base import Base
    url = "postgresql+psycopg2://pigos:pigos@localhost:5432/pigos"
    eng = create_engine(url)
    Base.metadata.create_all(eng)
    print("  스키마 create_all 완료")
    eng.dispose()


def verify_event_recency(pg, max_lag_days: int = 7) -> bool:
    """이관 후 게이트 — 이벤트별 최종일이 서로 크게 어긋나면 경고.

    사고 이력(2026-07/08): 07-22에 분만·이유만, 08-01에 교배만 이관 → 교배는 08-01까지
    있는데 분만은 07-20까지라 코호트 분만율이 0%로 계산됨. 반쪽 이관이 원인이었다.
    분만율은 "N일 전 교배가 분만했는가"를 보므로 교배가 분만보다 앞서면 실패로 잡힌다.

    임계 7일 근거: 실제 사고의 lag가 12일(교배 08-01 vs 분만 07-20)이었으므로 14일이면
    못 잡는다. 정상 이관은 같은 소스 스냅샷이라 lag가 며칠 이내여야 한다.
    """
    cur = pg.cursor()
    latest: dict[str, object] = {}
    for label, tbl, col in (("교배", "matings", "mating_date"),
                            ("분만", "farrowings", "farrowing_date"),
                            ("이유", "weanings", "weaning_date")):
        cur.execute(f"SELECT max({col}) FROM {tbl} WHERE deleted_at IS NULL")  # noqa: S608
        latest[label] = cur.fetchone()[0]
    print("\n[게이트] 이벤트별 최종일:", {k: str(v) for k, v in latest.items()})

    mating, farrow = latest.get("교배"), latest.get("분만")
    if not mating or not farrow:
        print("  ! 일부 이벤트가 비어 있음 — 검증 불가")
        return False
    lag = (mating - farrow).days
    if lag > max_lag_days:
        print(f"  !! 경고: 교배가 분만보다 {lag}일 앞섬(허용 {max_lag_days}일). "
              f"반쪽 이관 가능성 — 분만·이유도 같은 시점까지 이관해야 분만율이 정상 계산됨.")
        return False
    print(f"  OK: 교배-분만 간격 {lag}일 (허용 {max_lag_days}일 이내)")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--farm", type=int, help="단일 농장 파일럿")
    ap.add_argument("--all", action="store_true", help="42농장 전량")
    ap.add_argument("--bootstrap", action="store_true", help="스키마 먼저 생성")
    ap.add_argument("--prod", action="store_true", help="프로드 Supabase 타깃(PROD_PG_DSN)")
    ap.add_argument("--inspect", action="store_true", help="읽기전용 점검(카운트·컬럼)")
    ap.add_argument("--alter-columns", action="store_true", help="farms에 분류 컬럼 추가(추가전용)")
    args = ap.parse_args()

    global PG_DSN
    if args.prod:
        if not PROD_PG_DSN:
            sys.exit("PROD_PG_DSN 미설정 (api/.env 확인)")
        PG_DSN = PROD_PG_DSN
        print(f"[PROD] 타깃: {PROD_PG_DSN.split('host=')[1].split()[0]}")

    import psycopg2

    # ── 읽기전용 점검 (쓰기 없음) ──
    if args.inspect:
        cn = psycopg2.connect(PG_DSN); cur = cn.cursor()
        cur.execute("SELECT (SELECT count(*) FROM farms),(SELECT count(*) FROM sows),(SELECT count(*) FROM users)")
        print("farms/sows/users =", cur.fetchone())
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='farms' "
                    "AND column_name IN ('data_origin','data_classification')")
        cols = [r[0] for r in cur.fetchall()]
        print("분류 컬럼:", cols or "없음(--alter-columns 필요)")
        cur.execute("SELECT count(*) FROM farms WHERE farm_code LIKE 'PP-%'")
        print("기존 하베스트(PP-) 농장:", cur.fetchone()[0])
        cn.close(); return

    # ── 분류 컬럼 추가 (추가전용·멱등·안전) ──
    if args.alter_columns:
        cn = psycopg2.connect(PG_DSN); cur = cn.cursor()
        cur.execute("ALTER TABLE farms ADD COLUMN IF NOT EXISTS data_origin varchar(20) NOT NULL DEFAULT 'native_signup'")
        cur.execute("ALTER TABLE farms ADD COLUMN IF NOT EXISTS data_classification varchar(20) NOT NULL DEFAULT 'live_customer'")
        cn.commit(); cn.close()
        print("farms 분류 컬럼 추가 완료(IF NOT EXISTS)"); return

    if not ORACLE_PW:
        sys.exit("ORACLE_PW 환경변수 필수 (비밀값은 코드에 두지 않음)")

    if args.bootstrap:
        print("스키마 부트스트랩...")
        bootstrap_schema()

    import oracledb
    import psycopg2.extras
    psycopg2.extras.register_uuid()
    manifest = {int(m["source_farm_ref"]): m for m in build_manifest()}
    if args.farm:
        targets = [args.farm]
    elif args.all:
        targets = list(manifest.keys())
    else:
        print("--farm N 또는 --all 필요"); return

    import bcrypt
    pw_hash = bcrypt.hashpw(DEMO_PW.encode(), bcrypt.gensalt()).decode()  # 계정 공통(해시 1회)

    ora = oracledb.connect(user=ORACLE_USER, password=ORACLE_PW, dsn=ORACLE_DSN)
    ocur = ora.cursor()
    pg = psycopg2.connect(PG_DSN)

    grand = defaultdict(int)
    creds = []
    for fno in targets:
        m = manifest[fno]
        farm_id, org_id = ensure_farm(pg, m)
        creds.append(ensure_user(pg, farm_id, org_id, m, pw_hash))  # 계정가입
        src = fetch_farm(ocur, fno)
        R, stats = build_rows(fno, farm_id, src)
        upsert(pg, R)
        for k, v in stats.items():
            grand[k] += v
        print(f"farm {fno} [{m['country_code']}] {m['farm_name'][:20]:20} "
              f"sow={stats['sows']:5} cyc={stats['cycles']:6} mat={stats['matings']:6} "
              f"far={stats['farrowings']:6} wea={stats['weanings']:6} "
              f"(orphan far={stats['orphan_far']} wea={stats['orphan_wea']})")
    print("\n합계:", dict(grand))
    print(f"계정가입: {len(creds)}건 (공통 PW={DEMO_PW}), 예: {creds[0]['username']}/{creds[0]['email']}")
    verify_event_recency(pg)
    ora.close()
    pg.close()


if __name__ == "__main__":
    main()
