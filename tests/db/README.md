# PigOS DB 검증 환경

## 사전 조건
- Docker Desktop 실행 중

## 실행 방법

```bash
cd tests/db

# 1. 컨테이너 시작 (최초 실행 시 v1+v2 스키마 자동 적용 + 시드 데이터 삽입)
docker-compose up -d

# 2. 컨테이너 준비 확인 (healthy 상태 대기)
docker-compose ps

# 3. 검증 쿼리 실행
docker exec pigos-db-test psql -U pigos -d pigos_test \
    -f /docker-entrypoint-initdb.d/03_validate.sql

# 4. 직접 접속해서 쿼리
docker exec -it pigos-db-test psql -U pigos -d pigos_test

# 5. 컨테이너 + 볼륨 완전 초기화 (스키마 변경 후 재테스트 시)
docker-compose down -v && docker-compose up -d
```

## PigPlan 데이터 임포트

```bash
# CSV 파일을 tests/db/pigplan_data/ 에 복사 후
docker exec pigos-db-test psql -U pigos -d pigos_test \
    -f /pigplan_data/import.sql
```
→ [pigplan_import_guide.md](pigplan_import_guide.md) 참고

## 파일 구조

```
tests/db/
├── docker-compose.yml
├── README.md
├── pigplan_import_guide.md    ← PigPlan Oracle → PostgreSQL 임포트 가이드
├── pigplan_data/              ← PigPlan CSV 추출 파일 위치 (gitignore)
└── init/                      ← Docker 자동 실행 순서
    ├── 01_schema.sh           ← v1 + v2 스키마 적용
    ├── 02_seed_test.sql       ← 검증용 시드 데이터 (T-01~T-09 시나리오)
    └── 03_validate.sql        ← 검증 쿼리 10개
```
