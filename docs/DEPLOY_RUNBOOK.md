# PigOS 배포 런북 (실서버)

> 대상 서버: **52.78.65.6** (AWS Seoul). 구성: `docker-compose.prod.yml` (web·api·worker·redis·nginx) + 외부 PostgreSQL.
> 도메인: **app.pigos.io**(고객앱) · **api.pigos.io**(API) · **admin.pigos.io**(운영자 콘솔, 동일 web 호스트분기).
> ⚠️ 운영 작업 — 각 단계 확인 후 실행. 비밀값은 `.env`로만(레포 커밋 금지).

---

## 0. 사전 준비 (1회)
- [ ] EC2(Ubuntu) 접속, **Docker + docker compose plugin** 설치
- [ ] **보안그룹 인바운드**: 22(SSH, 내 IP) · 80 · 443 open
- [ ] **DNS A 레코드 3개** → 52.78.65.6 *(현재 admin만 설정됨 — app·api 추가 필요)*
  - `app.pigos.io` (또는 루트 `@`/`www` 리다이렉트) · `api.pigos.io` · `admin.pigos.io`
- [ ] **PostgreSQL 준비**: AWS RDS(권장) 또는 서버에 postgres 컨테이너 추가. `DATABASE_URL` 확보.
  - compose엔 postgres 서비스가 없음 → 외부 DB 전제. RDS면 보안그룹에서 EC2 접근 허용.

## 1. 코드 배포
```bash
ssh ubuntu@52.78.65.6
git clone <repo> pigos && cd pigos      # 최초 1회
# 이후 업데이트: git pull (main)
```

## 2. 환경변수 `.env` (레포 루트, compose가 읽음)
```bash
cat > .env <<'EOF'
DATABASE_URL=postgresql+asyncpg://USER:PASS@RDS_HOST:5432/pigos
REDIS_URL=redis://redis:6379
SECRET_KEY=<openssl rand -hex 32 로 생성>
ANTHROPIC_API_KEY=        # AI Insight(자연어) 쓸 때만, 없으면 템플릿 폴백
SENTRY_DSN=               # 선택
EOF
chmod 600 .env
```
> 확인: `web`은 `NEXT_PUBLIC_API_URL=https://api.pigos.io`로 빌드됨 → **API는 api.pigos.io로 직접 호출**.
> 따라서 **API CORS 허용 오리진**에 `https://app.pigos.io`, `https://admin.pigos.io` 포함됐는지 점검(api 설정).

## 3. SSL 인증서 (Let's Encrypt, 도메인 3개) — nginx 기동 전
nginx.conf가 `/etc/letsencrypt/live/{app,api,admin}.pigos.io/` 인증서를 참조하므로 **먼저 발급**:
```bash
sudo apt install certbot
# 80 포트 비어있는 상태에서 standalone 발급(최초)
sudo certbot certonly --standalone -d app.pigos.io -d api.pigos.io -d admin.pigos.io
# 갱신 자동화: certbot.timer 활성(또는 cron). 갱신 후 nginx reload 훅 등록.
```
(인증서 없으면 nginx가 뜨지 않으니 이 단계 먼저.)

## 4. DB 마이그레이션 + 시드
```bash
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
# 마스터 시드(질병/백신/벤치마크 등)
docker compose -f docker-compose.prod.yml run --rm api python scripts/seed_master.py
# 운영자(wiselake) 계정 — admin 콘솔 로그인용
docker compose -f docker-compose.prod.yml run --rm api python scripts/seed_admin.py
```

## 5. 기동
```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps     # web·api·worker·redis·nginx 모두 Up
```

## 6. 스모크 테스트
```bash
curl -I https://app.pigos.io/login          # 200
curl -s https://api.pigos.io/health          # {"status":"ok"...}
curl -I https://admin.pigos.io/login         # 200 (운영자 로그인)
```
- 브라우저: `app.pigos.io` 고객 로그인 / `admin.pigos.io` → `admin@pigos.io` 운영자 로그인 → `/admin` 콘솔.
- 비관리자가 admin 도메인 로그인 → "운영자 전용" 접근거부 화면(루프 없음) 확인.

## 7. 운영 체크리스트
- [ ] `.env` 권한 600, git 미추적
- [ ] API CORS: app/admin 오리진 허용
- [ ] DB 백업(RDS 자동백업 또는 pg_dump cron)
- [ ] certbot 자동갱신 + nginx reload 훅
- [ ] 로그: `docker compose logs -f web api worker nginx`
- [ ] 업데이트 절차: `git pull && docker compose -f docker-compose.prod.yml up -d --build` (+ 필요 시 alembic upgrade)

## 알려진 보강 포인트
- compose에 postgres 서비스 없음 → 외부 DB(RDS) 또는 postgres 서비스 추가 필요.
- `NEXT_PUBLIC_API_URL`이 절대 URL(api.pigos.io)이라 CORS 의존. (대안: 상대경로 + nginx `/api` 프록시로 동일출처화 — 현재 nginx는 도메인 분리 방식.)
