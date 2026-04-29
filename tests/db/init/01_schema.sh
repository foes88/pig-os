#!/bin/bash
# v1 + v2 스키마 순서대로 적용
set -e
echo "▶ Applying v1 schema..."
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /sql/2026-03-19_db-schema-v1.sql
echo "✔ v1 schema applied"

echo "▶ Applying v2 schema (config layer + CRITICAL fixes)..."
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /sql/2026-04-15_db-schema-v2.sql
echo "✔ v2 schema applied"
