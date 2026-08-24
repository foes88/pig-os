#!/usr/bin/env bash
# PigOS 일일 증분 백업 — Supabase egress 를 거의 쓰지 않고 손실 위험을 줄인다.
#
# 왜 필요한가: Supabase Free 플랜은 **자동 백업이 없다.** ops/backup_db.sh 의 주간 전체
# 덤프가 유일한 방어선이면 최악의 경우 7일치가 사라진다. 그런데 전체 덤프는 원본
# 825MB 를 전송하므로 매일 돌리면 월 25GB — Free egress 쿼터(5GB)를 5배 초과한다.
#
# 그래서 매일은 "최근 변경분"만 받는다. 하루 수 MB 수준이라 쿼터에 영향이 없다.
#   전체(주1회) + 증분(매일) → 손실 위험 7일 → 1일
#
# ★ created_at/updated_at 컬럼이 있는 테이블을 자동 탐색한다. 테이블 목록을 하드코딩하면
#   새 테이블이 생겼을 때 조용히 백업에서 빠진다.
# ★ 복원은 CSV → COPY 로 수동이다. 전체 덤프로 뼈대를 세우고 증분을 얹는 순서.
#   절차는 ops/ROLLBACK.md §E-3 참조.
#
# 사용:  ./backup_incremental.sh [일수]     기본 3일(겹치게 받아 누락 방지)
set -euo pipefail

DAYS="${1:-3}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/pigos-backups}"
INC_DIR="$BACKUP_DIR/incremental"
KEEP_DAYS="${KEEP_INC_DAYS:-14}"
ENV_FILE="${ENV_FILE:-$HOME/pigos/.env}"
PG_IMAGE="${PG_IMAGE:-postgres:17-alpine}"

mkdir -p "$INC_DIR"
[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE 없음"; exit 1; }
URL=$(grep -E '^DATABASE_URL=' "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '"'"'"'')
[ -n "$URL" ] || { echo "ERROR: DATABASE_URL 미설정"; exit 1; }
PGURL=$(printf '%s' "$URL" | sed -E 's#\+asyncpg##; s#\?ssl=require#?sslmode=require#')

sudo docker image inspect "$PG_IMAGE" >/dev/null 2>&1 || sudo docker pull -q "$PG_IMAGE"
PSQL=(sudo docker run --rm -i "$PG_IMAGE" psql "$PGURL" -qtAX)

TS=$(date +%Y%m%d-%H%M%S)
OUT="$INC_DIR/inc-$TS.tar.gz"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

echo "[$(date '+%F %T')] 증분 백업 (최근 ${DAYS}일)"

# 시점 컬럼이 있는 테이블 자동 탐색 — updated_at 우선(수정도 잡아야 한다)
TABLES=$("${PSQL[@]}" -c "
  SELECT c.table_name || ':' ||
         CASE WHEN bool_or(c.column_name='updated_at') THEN 'updated_at' ELSE 'created_at' END
  FROM information_schema.columns c
  JOIN information_schema.tables t
    ON t.table_name = c.table_name AND t.table_schema = c.table_schema
  WHERE c.table_schema='public' AND t.table_type='BASE TABLE'
    AND c.column_name IN ('created_at','updated_at')
  GROUP BY c.table_name ORDER BY 1")

[ -n "$TABLES" ] || { echo "ERROR: 시점 컬럼 있는 테이블을 못 찾음"; exit 1; }

TOTAL=0
for entry in $TABLES; do
  tbl="${entry%%:*}"; col="${entry##*:}"
  f="$WORK/$tbl.csv"
  if ! "${PSQL[@]}" -c "\\copy (SELECT * FROM public.$tbl WHERE $col >= now() - interval '$DAYS days') TO STDOUT WITH CSV HEADER" > "$f" 2>/dev/null; then
    echo "  ⚠ $tbl 건너뜀(조회 실패)"; rm -f "$f"; continue
  fi
  rows=$(( $(wc -l < "$f") - 1 ))
  if [ "$rows" -le 0 ]; then rm -f "$f"; continue
  fi
  TOTAL=$((TOTAL + rows))
  printf "  %-28s %6d행 (%s)\n" "$tbl" "$rows" "$col"
done

if [ "$TOTAL" -eq 0 ]; then
  echo "  변경분 없음 — 파일 생성 생략"; exit 0
fi

tar -czf "$OUT" -C "$WORK" .
echo "[$(date '+%F %T')] 완료 $(du -h "$OUT" | cut -f1) / 총 ${TOTAL}행"

find "$INC_DIR" -name 'inc-*.tar.gz' -mtime +"$KEEP_DAYS" -print -delete 2>/dev/null || true
