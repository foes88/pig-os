#!/usr/bin/env bash
# PigOS 프로덕션 DB 백업 — Supabase 독립 사본.
#
# 왜 필요한가: 2026-08-24 배포 사고 때 롤백 이미지가 사라져 되돌릴 수단이 없었고,
# DB 백업 상태도 확인되지 않았다. Supabase 자체 백업이 1차 방어선이고, 이건 그 계정
# 자체에 문제가 생겼을 때를 위한 독립 사본이다.
#
# ★ 전송량 주의: pg_dump 는 데이터를 원본 크기(약 825MB)로 받아 로컬에서 압축한다.
#   Supabase egress 쿼터를 먹으므로 full 은 주 1회 + 배포 직전으로 제한한다.
#
# 사용:
#   ./backup_db.sh schema      스키마만 (수십 KB, 매일)
#   ./backup_db.sh full        전체 (약 100~150MB 압축, 주 1회/배포 직전)
#   ./backup_db.sh full deploy 배포 직전용 — 파일명에 표시하고 보존기간에서 제외
set -euo pipefail

MODE="${1:-full}"
TAG="${2:-}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/pigos-backups}"
KEEP_DAYS="${KEEP_DAYS:-7}"
ENV_FILE="${ENV_FILE:-$HOME/pigos/.env}"

mkdir -p "$BACKUP_DIR"

# DATABASE_URL 은 .env 에서만 읽는다 — 스크립트에 자격증명을 두지 않는다.
[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE 없음"; exit 1; }
URL=$(grep -E '^DATABASE_URL=' "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '"'"'"'')
[ -n "$URL" ] || { echo "ERROR: DATABASE_URL 미설정"; exit 1; }
# SQLAlchemy 드라이버 표기를 libpq 가 이해하는 형태로
PGURL=$(printf '%s' "$URL" | sed -E 's#\+asyncpg##; s#\?ssl=require#?sslmode=require#')

TS=$(date +%Y%m%d-%H%M%S)
SUFFIX="${TAG:+-$TAG}"
OUT="$BACKUP_DIR/pigos-$MODE-$TS$SUFFIX.sql.gz"

# 디스크 여유 확인 — full 은 넉넉히 1GB 는 있어야 안전하다.
AVAIL_MB=$(df -Pm "$BACKUP_DIR" | awk 'NR==2{print $4}')
NEED_MB=$([ "$MODE" = "full" ] && echo 1024 || echo 50)
if [ "$AVAIL_MB" -lt "$NEED_MB" ]; then
  echo "ERROR: 디스크 부족 (${AVAIL_MB}MB 남음, ${NEED_MB}MB 필요)"; exit 1
fi

case "$MODE" in
  schema) ARGS=(--schema-only) ;;
  full)   ARGS=() ;;
  *)      echo "usage: $0 {schema|full} [tag]"; exit 2 ;;
esac

# ★ pg_dump 는 서버보다 낮은 버전이면 거부한다(Supabase = PG 17.6, 우분투 기본 = 16.x).
#   호스트에 apt 로 깔지 않고 버전 고정 컨테이너를 쓴다 — 운영 서버 상태를 안 바꾼다.
PG_IMAGE="${PG_IMAGE:-postgres:17-alpine}"
if command -v pg_dump >/dev/null 2>&1 &&    [ "$(pg_dump --version | grep -oE '[0-9]+' | head -1)" -ge 17 ]; then
  DUMP=(pg_dump)
else
  sudo docker image inspect "$PG_IMAGE" >/dev/null 2>&1 || sudo docker pull -q "$PG_IMAGE"
  DUMP=(sudo docker run --rm -i "$PG_IMAGE" pg_dump)
fi

echo "[$(date '+%F %T')] $MODE 백업 시작 → $OUT"
echo "  덤프 도구: ${DUMP[*]}"
# --no-owner/--no-acl: Supabase 롤 구성이 복원 대상과 다를 수 있어 소유권을 빼둔다.
if ! "${DUMP[@]}" "$PGURL" --no-owner --no-acl "${ARGS[@]}" | gzip -9 > "$OUT"; then
  echo "ERROR: pg_dump 실패"; rm -f "$OUT"; exit 1
fi

SIZE=$(du -h "$OUT" | cut -f1)
# 빈 덤프(연결은 됐는데 내용이 없는 경우)를 성공으로 넘기지 않는다.
LINES=$(gzip -dc "$OUT" | head -50 | grep -c . || true)
if [ "$LINES" -lt 5 ]; then
  echo "ERROR: 덤프 내용이 비정상적으로 적음 — 실패로 처리"; rm -f "$OUT"; exit 1
fi
echo "[$(date '+%F %T')] 완료 $SIZE"

# 보존 정리 — deploy 태그가 붙은 것은 지우지 않는다(되돌릴 지점이라 오래 남긴다).
find "$BACKUP_DIR" -name 'pigos-*.sql.gz' ! -name '*-deploy.sql.gz' \
     -mtime +"$KEEP_DAYS" -print -delete 2>/dev/null || true

echo "보관 현황:"; ls -lh "$BACKUP_DIR" | tail -8
