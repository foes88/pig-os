# PigOS Go-Live 런북

> 운영 배포 절차. **인프라 실행(DNS·EC2·SSL·DB)은 사람이 수행** — 이 문서는 순서/명령 체크리스트.
> 대상: app.pigos.io(웹) + api.pigos.io(API), EC2 52.78.65.6, DB = Supabase(외부).
> 산출물: `docker-compose.prod.yml`, `deploy/setup.sh`, `nginx/nginx.conf`. 최종 갱신 2026-06-16.

---

## 아키텍처 (prod)
```
인터넷 → nginx(443/SSL) ┬→ web (Next.js standalone, :3000)
                        └→ api (FastAPI uvicorn, :8000)
                           worker (ARQ cron) ── redis
                           api/worker → Supabase Postgres (외부)
```
> 웹은 **Docker(standalone)** 로 배포 — Vercel 미사용(`vercel.json` 불필요).

---

## 0. 사전 준비 (1회)
- [ ] 가비아 DNS A 레코드: `app.pigos.io → 52.78.65.6`, `api.pigos.io → 52.78.65.6`
- [ ] Supabase 프로젝트 + DB 비밀번호 확보
- [ ] EC2(ubuntu) 접속 가능, Docker/Compose 설치 (`deploy/setup.sh` 참고)

## 1. 서버 셋업
```bash
ssh ubuntu@52.78.65.6
git clone <repo> pigos && cd pigos
bash deploy/setup.sh          # docker, certbot 설치 등
```

## 2. 환경변수 (.env — 서버에만, 커밋 금지)
```bash
DATABASE_URL=postgresql+asyncpg://postgres:<PW>@db.<REF>.supabase.co:5432/postgres
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<python -c "import secrets;print(secrets.token_hex(32))">
# 선택(미설정 시 graceful fallback):
ANTHROPIC_API_KEY=         # Addon #1 AI Insight
FCM_PROJECT_ID=            # G1 푸시 (google-auth 설치 필요)
FCM_CREDENTIALS_PATH=      # 서비스계정 JSON 경로(컨테이너 내)
SENTRY_DSN=
```

## 3. DB 마이그레이션 (⚠️ 필수 — 신규 테이블 반영)
> 운영 DB(Supabase)에 최신 스키마 적용. 최근 추가분: `tasks`, `devices`, sow status v2 등.
```bash
# api 컨테이너 빌드 후 1회 실행 (또는 로컬에서 prod DATABASE_URL로):
docker compose -f docker-compose.prod.yml run --rm api uv run alembic upgrade head
# 적용 확인:
docker compose -f docker-compose.prod.yml run --rm api uv run alembic current
```

## 4. SSL 인증서 (DNS 전파 후)
```bash
sudo certbot certonly --standalone -d app.pigos.io -d api.pigos.io \
  --email jhbae@wiselake.co.kr --agree-tos
```

## 5. 기동
```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps     # web/api/worker/redis/nginx 모두 Up
```
> **worker 컨테이너 Up 확인**(G3) — KPI 집계 + Task(05:30) + 알림(06:00) cron 실행 주체.

## 6. 스모크 테스트 (go/no-go)
- [ ] `curl https://api.pigos.io/health` → `{"status":"ok"}`
- [ ] `https://app.pigos.io` 로그인 화면 200
- [ ] 로그인 → 대시보드 KPI 로드
- [ ] `curl https://api.pigos.io/api/v1/.../health` 무관 — OpenAPI: `https://api.pigos.io/docs`(운영은 비활성일 수 있음)
- [ ] worker 로그: `docker compose -f docker-compose.prod.yml logs worker | tail`

## 7. 배포 후 선택 활성화
- **FCM 푸시(G1)**: api Dockerfile에 `google-auth` 추가(`uv add google-auth`) + 서비스계정 JSON 마운트 + 2번 env → 재배포.
- **AI Insight**: `ANTHROPIC_API_KEY` 설정 → 해당 농장 addon 활성 시 LLM 응답.

---

## 롤백
```bash
git checkout <이전태그> && docker compose -f docker-compose.prod.yml up -d --build
# DB는 마이그레이션 downgrade 신중히: alembic downgrade -1 (데이터 영향 검토 필수)
```

## 미해결/주의
- **G4** sync 실단말 E2E는 모바일 출시 전 별도 검증(계약서 §6).
- 운영 DB 마이그레이션은 **백업 후** 수행 권장(Supabase 자동백업 확인).
- `deploy/setup.sh`의 IP/도메인/이메일은 환경에 맞게 확인.
