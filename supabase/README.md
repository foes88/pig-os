# Supabase 마이그레이션 가이드

## 구조

```
supabase/
├── migrations/
│   └── 20260605000000_init_full_schema.sql  ← 전체 스키마 (Alembic base→head)
└── README.md
```

## 적용 방법

### 방법 A — Alembic으로 직접 연결 (권장)

Supabase 프로젝트 → Settings → Database → Connection string (URI) 복사 후:

```bash
# api/.env 또는 환경변수에 설정
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres

# 전체 마이그레이션 적용
cd api
uv run alembic upgrade head
```

### 방법 B — SQL 파일 직접 실행

Supabase Dashboard → SQL Editor 에서 아래 파일 내용을 붙여넣고 실행:

```
supabase/migrations/20260605000000_init_full_schema.sql
```

> ⚠️ 이미 테이블이 일부 있는 경우 방법 A를 사용하세요.

## 환경 변수 (.env)

```env
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
REDIS_URL=redis://...
SECRET_KEY=...
```

## 마이그레이션 이력

| Revision | 내용 |
|----------|------|
| f36cde9d762c | 초기 스키마 (40+ 테이블) |
| a7cda1c25637 | 확장 스키마 |
| 1cbe4adb7e13 | 추가 |
| 6cbf1c758818 | 추가 |
| a1273623b95d | 조직 계층 + 권한 시스템 (system_role) |
| b6f6e3a9c2d1 | KPI 뷰 + effective_metric_values() |
| c7d4e2a1f9b0 | scope_code VARCHAR(50) 확장 |
| e3f9a2b4c8d1 | Rule Engine 임계값 + 5개국 데이터 |

## 주의사항

- `alembic upgrade head`는 **반드시 운영 DB 적용 전 로컬에서 먼저 검증**
- 로컬 검증 완료 상태: `e3f9a2b4c8d1 (head)` ✅
- Supabase 적용은 **개발자 직접 승인 후 실행**
