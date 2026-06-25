# PigOS DB 인프라 전략 & 향후 방향

> 최종 갱신: 2026-06-25
> 결정권자: 사용자(jhbae) · 구현: Claude/Codex 세션
> 원칙: 운영 DB 데이터 직접 변경 금지(스키마 마이그레이션은 허가 시) · 정합성 최우선.

---

## 1. 현재 상태 (2026-06)
| 항목 | 값 |
|------|-----|
| DB | **Supabase 무료 티어** (PostgreSQL 16) |
| 접속 | pooler `aws-1-ap-northeast-2.pooler.supabase.com` (서울) |
| 리전 | ap-northeast-2 (서울) — 앱 서버 EC2와 동일 리전 |
| alembic head | `b3d5f7091a2c` |
| 앱 서버 | 공유 EC2 52.78.65.6 (docker compose: web/api/worker/redis) |

### 무료 티어 한계 (인지 필요)
- **용량 500MB** (DB) — 농장·이벤트 데이터 누적 시 가장 먼저 닿는 한계
- **7일 무활동 시 auto-pause** → ✅ **해결됨**(아래 2번)
- **백업 7일** 보관 (PITR 없음)
- 대역폭 5GB/월

---

## 2. auto-pause 방지 (구현 완료 2026-06-25)
무료 티어는 7일간 DB 쿼리가 없으면 프로젝트를 자동 정지한다. 운영 서버는 항상 살아있어야 하므로 방지함.

**구현**: `api/app/jobs/keepalive.py` → `db_keepalive` (매일 12:00 UTC `SELECT 1`).
- worker cron 등록: `app/jobs/worker.py`
- 기존 KPI/알림 cron(00:05·05:30·06:00 UTC)도 DB를 치지만, 농장 데이터가 없으면 일부 쿼리가 비어 "무활동"으로 분류될 여지가 있어 **명시적 keep-alive를 12:00에 별도 배치**(시간대 분산).
- 유료 전환 후에도 무해 → 그대로 유지.

> 검증: worker 로그에 `[keepalive] db ping ok` 가 매일 1회 찍히면 정상.

---

## 3. 향후 방향 (성장 단계별)

### 단계 0 — 지금 (출시 ~ 초기 파일럿)
- **Supabase 무료 유지.** 비용 0, 코드 변경 0.
- 모니터링만: Supabase 대시보드에서 **DB 용량(500MB 대비 %)** 주시.

### 단계 1 — 가입자/데이터 증가 시 → **Supabase Pro**
- 트리거(아래 중 하나): DB 용량 **>400MB(80%)** · 실사용 농장 다수 · 백업/PITR 필요
- **Supabase Pro** $25/월: 8GB DB · 일별 백업 + 7일 PITR · 무정지 · 더 큰 대역폭
- **전환 비용 거의 0**: 같은 Supabase 프로젝트 업그레이드 → **DATABASE_URL 그대로, 코드 변경 없음, 마이그레이션 불필요.** 콘솔에서 플랜만 변경.

### 단계 2 — 엔터프라이즈/규모 확대 시 → **AWS RDS(서울) 검토**
- 트리거: 대형 고객 · 멀티 read replica · VPC 격리 · 세밀한 튜닝 필요
- **AWS RDS PostgreSQL** (ap-northeast-2): 관리형, 스케일·백업·모니터링 우수, EC2와 동일 VPC 가능
- 비용 ↑ + 마이그레이션 작업 필요(pg_dump/restore + DATABASE_URL 교체). **데이터 양 적을 때 미리 옮기는 게 유리**하므로 단계1↔2 타이밍은 데이터 증가 추이 보고 결정.

### 대안(참고, 현재 비채택)
- **EC2 self-host postgres**: $0 추가지만 백업·장애복구·보안패치 전부 수동 → 운영 리스크. 비추.
- **Neon(서버리스)**: 무료티어 넉넉·자동 스케일. Supabase에서 이미 운영 중이라 전환 이득 작음.

---

## 4. 의사결정 요약
| 질문 | 결론 |
|------|------|
| 지금 무료로 출시해도 되나? | **O** — 무료로 출시, auto-pause는 keep-alive로 방지됨 |
| 언제 유료로? | DB **용량 80%** 또는 가입자 증가 시 → **Supabase Pro($25)**, 코드 0 |
| RDS는? | 엔터프라이즈/대규모 단계에서 검토(데이터 적을 때 이전 유리) |
| 데이터 계속 무료로 쌓이나? | 500MB까지 무료. 초과 전 Pro 전환 필요 |

---

## 5. 관련 파일
- `api/app/jobs/keepalive.py` — auto-pause 방지 잡
- `api/app/jobs/worker.py` — cron 등록
- `api/app/core/config.py` — `database_url` / `redis_url`
- `docker-compose.deploy.yml` — 운영 override(포트 3010/8010)
- `handoff/VERIFICATION_HANDOFF_for_codex.md` — 검증·배포 메모
