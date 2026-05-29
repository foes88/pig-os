"""
PigPlan Oracle CSV → PigOS PostgreSQL 임포트 스크립트
- Oracle: FARM_NO + PIG_NO 복합키 구조
- PigOS: UUID 기반 구조
- 목적: PSY/NPD 계산 정합성 검증
"""

import csv
import uuid
import psycopg2
from datetime import datetime, date
from pathlib import Path

DATA_DIR = Path(__file__).parent
PG_DSN = "host=localhost port=5433 dbname=pigos_test user=pigos password=pigos_dev"

# ── 코드 매핑 ────────────────────────────────────────────────────
STATUS_MAP = {
    '010001': 'ACTIVE',       # 후보돈
    '010002': 'GESTATING',    # 임신돈
    '010003': 'LACTATING',    # 분만돈
    '010004': 'WEANED',       # 이유돈
    '010006': 'GESTATING',    # 재교배임신돈
    '010007': 'GESTATING',    # 기타임신돈
}
OUT_STATUS_MAP = {
    '080001': 'CULLED',       # 도태
    '080002': 'DEAD',         # 폐사
    '080003': 'CULLED',       # 임돈전출
    '080004': 'CULLED',       # 임돈판매
}
SAGO_MAP = {
    '050001': 'RETURN_ESTRUS',
    '050002': 'RETURN_ESTRUS',  # 재발
    '050003': 'ABORT',
    '050004': 'ABORT',
    '050005': 'ABORT',
    '050006': 'ABORT',
}

def parse_date(s):
    """YYYYMMDD / YYYY-MM-DD / DATE 객체 → date"""
    if s is None:
        return None
    if isinstance(s, (date, datetime)):
        d = s.date() if isinstance(s, datetime) else s
        return None if d.year >= 9999 else d
    s = str(s).strip()
    if not s or s in ('', 'None'):
        return None
    try:
        if '-' in s:
            d = datetime.strptime(s[:10], '%Y-%m-%d').date()
        else:
            d = datetime.strptime(s[:8], '%Y%m%d').date()
        return None if d.year >= 9999 else d
    except:
        return None

def load_csv(filename):
    with open(DATA_DIR / filename, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def main():
    conn = psycopg2.connect(PG_DSN)
    conn.autocommit = False
    cur = conn.cursor()

    # 대량 임포트 중 row-level 트리거 비활성화 (sows UPDATE 50만번 방지)
    cur.execute("SET session_replication_role = replica;")
    conn.commit()

    print("PigOS 기존 피그플랜 데이터 정리...")
    cur.execute("DELETE FROM organizations WHERE id::text LIKE 'PIGPLAN%'")

    # ── 1. 농장 목록 로드 ────────────────────────────────────────
    print("[1/6] 농장/조직 생성...")
    farms_csv = load_csv('farms.csv')
    farm_uuid_map = {}   # farm_no → UUID

    # 피그플랜 통합 조직 생성 (UUID에 hex만 사용)
    org_id = 'a1b2c3d4-0000-0000-0000-000000000001'
    cur.execute("""
        INSERT INTO organizations (id, name, country)
        VALUES (%s, '피그플랜 PSY상위35개농장', 'KR')
        ON CONFLICT (id) DO NOTHING
    """, (org_id,))

    for row in farms_csv:
        farm_no = row['farm_no']
        farm_name = row['farm_name']
        fid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f'pigplan.farm.{farm_no}'))
        farm_uuid_map[int(farm_no)] = fid
        cur.execute("""
            INSERT INTO farms (id, org_id, farm_code, name, country, region, timezone)
            VALUES (%s, %s, %s, %s, 'KR', 'KR', 'Asia/Seoul')
            ON CONFLICT (id) DO NOTHING
        """, (fid, org_id, f'PP-{farm_no}', farm_name))

    conn.commit()
    print(f"  → 조직 1개, 농장 {len(farm_uuid_map)}개 생성")

    # ── 2. 모돈 임포트 ───────────────────────────────────────────
    print("[2/6] 모돈(sows) 임포트...")
    sows_csv = load_csv('sows.csv')
    sow_uuid_map = {}    # (farm_no, pig_no) → UUID

    batch = []
    skipped = 0
    for row in sows_csv:
        farm_no = int(row['farm_no'])
        pig_no = int(row['pig_no'])
        farm_id = farm_uuid_map.get(farm_no)
        if not farm_id:
            skipped += 1
            continue

        entry_dt = parse_date(row['in_dt'])
        if not entry_dt:
            skipped += 1
            continue

        out_dt = parse_date(row['out_dt'])
        out_cd = row.get('out_gubun_cd', '')
        status_cd = row.get('status_cd', '')

        if out_dt and out_cd in OUT_STATUS_MAP:
            status = OUT_STATUS_MAP[out_cd]
        else:
            status = STATUS_MAP.get(status_cd, 'ACTIVE')

        sow_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f'pigplan.sow.{farm_no}.{pig_no}'))
        sow_uuid_map[(farm_no, pig_no)] = sow_id  # 검증 통과 후 맵 등록

        entry_type = 'GILT' if row.get('in_sancha', '0') in ('0', '') else 'TRANSFER'

        batch.append((
            sow_id, farm_id,
            str(pig_no),   # pig_no = PigPlan 내부 고유키, farm_pig_no는 재사용 가능
            row.get('pumjong_cd') or 'UNKNOWN',
            int(row['in_sancha']) if row.get('in_sancha') else 0,
            status,
            entry_dt,
            out_dt,
            entry_type,
        ))

        if len(batch) >= 2000:
            cur.executemany("""
                INSERT INTO sows
                  (id, farm_id, ear_tag, breed, parity, status, entry_date, exit_date, entry_type)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO NOTHING
            """, batch)
            batch = []

    if batch:
        cur.executemany("""
            INSERT INTO sows
              (id, farm_id, ear_tag, breed, parity, status, entry_date, exit_date, entry_type)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO NOTHING
        """, batch)

    conn.commit()
    print(f"  → 모돈 {len(sow_uuid_map):,}건 임포트 (스킵: {skipped})")

    # sow count 업데이트
    cur.execute("""
        UPDATE farms f
        SET active = TRUE  -- sow_count 컬럼 없음 (v1 스키마)
        WHERE f.org_id = %s
    """, (org_id,))
    conn.commit()

    # ── 3. 교배 임포트 ───────────────────────────────────────────
    print("[3/6] 교배(matings) 임포트...")
    matings_csv = load_csv('matings.csv')
    mating_uuid_map = {}  # (farm_no, pig_no, seq) → UUID

    batch = []
    skipped = 0
    for row in matings_csv:
        farm_no = int(row['farm_no'])
        pig_no = int(row['pig_no'])
        seq = int(row['seq'])
        sow_id = sow_uuid_map.get((farm_no, pig_no))
        farm_id = farm_uuid_map.get(farm_no)
        if not sow_id:
            skipped += 1
            continue

        mid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f'pigplan.mating.{farm_no}.{pig_no}.{seq}'))
        mating_uuid_map[(farm_no, pig_no, seq)] = mid
        mtype = row.get('mating_type', 'A')
        mating_type = 'AI' if mtype in ('A', 'a', '1') else 'NATURAL'
        mating_dt = parse_date(row['mating_dt'])
        if not mating_dt:
            skipped += 1
            continue

        batch.append((
            mid, farm_id, sow_id,
            mating_dt,
            min(int(row['gyobae_cnt']), 5) if row.get('gyobae_cnt') and row['gyobae_cnt'].strip() else 1,
            mating_type,
        ))

        if len(batch) >= 5000:
            cur.executemany("""
                INSERT INTO matings
                  (id, farm_id, sow_id, mating_date, mating_number, mating_type)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO NOTHING
            """, batch)
            batch = []

    if batch:
        cur.executemany("""
            INSERT INTO matings
              (id, farm_id, sow_id, mating_date, mating_number, mating_type)
            VALUES (%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO NOTHING
        """, batch)

    conn.commit()
    print(f"  → 교배 {len(mating_uuid_map):,}건 임포트 (스킵: {skipped})")

    # mating 역방향 인덱스: (farm_no, pig_no, sancha) → latest mating_uuid
    # G.SANCHA = 교배 시점 산차, B.SANCHA = G.SANCHA + 1
    mating_by_sancha = {}  # (farm_no, pig_no, sancha) → (seq, uuid)
    for (fn, pn, seq), mid in mating_uuid_map.items():
        pass  # 아래에서 matings_csv 재로드로 처리

    # matings_csv 재로드하여 SANCHA 인덱스 구축
    for row in matings_csv:
        fn = int(row['farm_no'])
        pn = int(row['pig_no'])
        seq = int(row['seq'])
        sancha = int(row['sancha']) if row.get('sancha') else 0
        mid = mating_uuid_map.get((fn, pn, seq))
        if not mid:
            continue
        key = (fn, pn, sancha)
        existing = mating_by_sancha.get(key)
        # 같은 산차 내 재교배 시 GYOBAE_CNT 높은 것 (마지막 교배) 선택
        gyobae_cnt = int(row['gyobae_cnt']) if row.get('gyobae_cnt') else 1
        if not existing or gyobae_cnt > existing[0]:
            mating_by_sancha[key] = (gyobae_cnt, mid)

    # ── 4. 분만 임포트 ───────────────────────────────────────────
    print("[4/6] 분만(farrowings) 임포트...")
    farrowings_csv = load_csv('farrowings.csv')
    farrowing_uuid_map = {}  # (farm_no, pig_no, sancha) → UUID

    batch = []
    skipped = 0
    for row in farrowings_csv:
        farm_no = int(row['farm_no'])
        pig_no = int(row['pig_no'])
        seq = int(row['seq'])
        sow_id = sow_uuid_map.get((farm_no, pig_no))
        farm_id = farm_uuid_map.get(farm_no)
        if not sow_id:
            skipped += 1
            continue

        farrowing_dt = parse_date(row['farrowing_dt'])
        if not farrowing_dt:
            skipped += 1
            continue

        # B.SANCHA = G.SANCHA + 1 → mating_sancha = farrowing_sancha - 1
        farrowing_sancha = int(row['sancha']) if row.get('sancha') else 1
        mating_sancha = farrowing_sancha - 1
        mating_entry = mating_by_sancha.get((farm_no, pig_no, mating_sancha))
        if not mating_entry:
            skipped += 1
            continue
        mating_id = mating_entry[1]

        fid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f'pigplan.farrowing.{farm_no}.{pig_no}.{seq}'))
        farrowing_uuid_map[(farm_no, pig_no, farrowing_sancha)] = fid

        born_alive = int(row['born_alive']) if row.get('born_alive') else 0
        mummified = int(row['mummified']) if row.get('mummified') else 0
        stillborn = int(row['stillborn']) if row.get('stillborn') else 0
        total_born = born_alive + mummified + stillborn

        batch.append((
            fid, farm_id, sow_id, mating_id,
            farrowing_dt, farrowing_sancha,
            total_born, born_alive, stillborn, mummified,
        ))

        if len(batch) >= 5000:
            cur.executemany("""
                INSERT INTO farrowings
                  (id, farm_id, sow_id, mating_id, farrowing_date, parity_at_birth,
                   total_born, born_alive, stillborn, mummified)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO NOTHING
            """, batch)
            batch = []

    if batch:
        cur.executemany("""
            INSERT INTO farrowings
              (id, farm_id, sow_id, mating_id, farrowing_date, parity_at_birth,
               total_born, born_alive, stillborn, mummified)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO NOTHING
        """, batch)

    conn.commit()
    print(f"  → 분만 {len(farrowing_uuid_map):,}건 임포트 (스킵: {skipped})")

    # ── 5. 이유 임포트 ───────────────────────────────────────────
    print("[5/6] 이유(weanings) 임포트...")
    weanings_csv = load_csv('weanings.csv')

    batch = []
    skipped = 0
    weaning_count = 0
    for row in weanings_csv:
        farm_no = int(row['farm_no'])
        pig_no = int(row['pig_no'])
        seq = int(row['seq'])
        sow_id = sow_uuid_map.get((farm_no, pig_no))
        farm_id = farm_uuid_map.get(farm_no)
        if not sow_id:
            skipped += 1
            continue

        weaning_dt = parse_date(row['weaning_dt'])
        if not weaning_dt:
            skipped += 1
            continue

        # E.SANCHA = B.SANCHA → 같은 산차 분만 기록 연결
        weaning_sancha = int(row['sancha']) if row.get('sancha') else 1
        farrowing_id = farrowing_uuid_map.get((farm_no, pig_no, weaning_sancha))

        if not farrowing_id:
            skipped += 1
            continue

        wid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f'pigplan.weaning.{farm_no}.{pig_no}.{seq}'))
        weaned_count = int(row['weaned_count']) if row.get('weaned_count') else 0
        _age = int(float(row['weaning_age_days'])) if row.get('weaning_age_days') else None
        weaning_age = _age if _age and 1 <= _age <= 60 else None  # 범위 밖은 NULL (오데이터)

        batch.append((
            wid, farm_id, sow_id, farrowing_id,
            weaning_dt, weaned_count, weaning_age,
        ))
        weaning_count += 1

    # farrowing_id 기준 dedup (PigPlan에 동일 분만 이유 중복 가능) — 첫 번째만 유지
    seen_farrowings = set()
    deduped = []
    for row_tuple in batch:
        fid_key = row_tuple[3]  # farrowing_id
        if fid_key not in seen_farrowings:
            seen_farrowings.add(fid_key)
            deduped.append(row_tuple)

    if deduped:
        cur.executemany("""
            INSERT INTO weanings
              (id, farm_id, sow_id, farrowing_id, weaning_date, weaned_count, weaning_age_days)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO NOTHING
        """, deduped)

    conn.commit()
    print(f"  → 이유 {weaning_count:,}건 임포트 (스킵: {skipped})")

    # ── 6. 요약 검증 ─────────────────────────────────────────────
    print("\n[6/6] 임포트 결과 검증...")
    cur.execute("SELECT COUNT(*) FROM farms WHERE org_id = %s", (org_id,))
    print(f"  농장: {cur.fetchone()[0]:,}개")
    cur.execute("""
        SELECT COUNT(*) FROM sows s
        JOIN farms f ON f.id = s.farm_id
        WHERE f.org_id = %s
    """, (org_id,))
    print(f"  모돈: {cur.fetchone()[0]:,}건")
    cur.execute("""
        SELECT COUNT(*) FROM matings m
        JOIN farms f ON f.id = m.farm_id
        WHERE f.org_id = %s
    """, (org_id,))
    print(f"  교배: {cur.fetchone()[0]:,}건")
    cur.execute("""
        SELECT COUNT(*) FROM farrowings fa
        JOIN farms f ON f.id = fa.farm_id
        WHERE f.org_id = %s
    """, (org_id,))
    print(f"  분만: {cur.fetchone()[0]:,}건")
    cur.execute("""
        SELECT COUNT(*) FROM weanings w
        JOIN farms f ON f.id = w.farm_id
        WHERE f.org_id = %s
    """, (org_id,))
    print(f"  이유: {cur.fetchone()[0]:,}건")

    # 트리거 복원
    cur.execute("SET session_replication_role = DEFAULT;")
    conn.commit()

    cur.close()
    conn.close()
    print("\n✓ 임포트 완료")


if __name__ == '__main__':
    main()
