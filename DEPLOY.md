# PigOS 프로덕션 배포 가이드

실제 운영 중인 배포 구성 (2026-06 기준). 서버: **AWS EC2 `52.78.65.6` (ubuntu)**, 단일 인스턴스.

## 1. 아키텍처 (도메인 → 서비스)

| 도메인 | 대상 | 실행 형태 | 포트 |
|---|---|---|---|
| `pigos.io` / `www.pigos.io` | 랜딩 (Astro, 별도 레포 `pigos-landing`) | pm2 `pigos-landing` | 127.0.0.1:4000 |
| `app.pigos.io` | 웹앱 (Next.js, `src/`) | Docker `pigos-web` | 127.0.0.1:3010 |
| `api.pigos.io` | API (FastAPI, `api/`) | Docker `pigos-api` | 127.0.0.1:8010 |
| — | ARQ 워커 (cron) | Docker `pigos-worker` | — |
| — | Redis | Docker `pigos-redis` | (내부) |
| — | DB | **Supabase** (외부 관리형 Postgres) | — |

> **시스템 nginx**(host)가 80/443을 점유하며 모든 vhost를 프록시한다. Compose의 nginx 서비스는 **사용하지 않는다**(포트 충돌 방지). `pigsignal.*` 도 같은 nginx에서 서빙됨.

## 2. 디렉토리

- 랜딩: `/home/ubuntu/pigos-landing` (dist 파일복사형, git 아님)
- 앱: `/home/ubuntu/pigos` (코드 복사형, git 아님 — deploy key 미설정)
- nginx vhost: `/etc/nginx/sites-available/{pigos.io, pigos-app, pigsignal}`
- 인증서: `/etc/letsencrypt/live/{pigos.io, app.pigos.io, ...}`

## 3. 앱 배포 (app.pigos.io / api.pigos.io)

### 3.1 코드 전송 (시크릿 제외)
로컬에서:
```bash
cd <PigOS 로컬>
tar czf /tmp/pigos-app.tgz \
  --exclude='api/.env' --exclude='api/.env.*' \
  --exclude='src/.env.local' --exclude='src/.env*.local' \
  --exclude='src/node_modules' --exclude='src/.next' --exclude='src/test-results' \
  --exclude='api/.venv' --exclude='**/__pycache__' --exclude='.git' \
  docker-compose.prod.yml src api nginx
scp -i <key> /tmp/pigos-app.tgz ubuntu@52.78.65.6:/tmp/
ssh ... 'cd /home/ubuntu/pigos && tar xzf /tmp/pigos-app.tgz && rm /tmp/pigos-app.tgz'
```
> `src/.env.production`(공개 URL: api.pigos.io)은 **포함**되어야 Next 빌드가 올바른 API URL을 굽는다.

### 3.2 환경변수 — `/home/ubuntu/pigos/.env` (chmod 600, git에 절대 커밋 금지)
```
DATABASE_URL=postgresql+asyncpg://postgres.<ref>:<supabase-pw>@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?ssl=require
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<python3 -c "import secrets;print(secrets.token_hex(32))">
ENVIRONMENT=production
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```
> compose가 기본으로 `.env`를 읽어 `${VAR}` 치환 + 컨테이너에 주입.

> ⚠️ **반드시 Supabase IPv4 세션 풀러 사용 (직접연결 금지).** Supabase 직접연결
> `db.<ref>.supabase.co`는 **IPv6 전용**인데 이 EC2는 IPv4뿐이라 `Network is unreachable`로
> 실패한다. 대시보드 → Connect → Direct → **Session pooler** 값을 써야 함:
> - 호스트 `aws-1-ap-northeast-2.pooler.supabase.com` (리전별 `aws-0`/`aws-1` 다름 — 대시보드 확인)
> - 유저명 `postgres.<project_ref>` (예: `postgres.hrbfvaectsopqttbhpnr`)
> - 포트 `5432`(세션 모드, asyncpg prepared statement 호환). 트랜잭션 6543 ✕
> - `?ssl=require` (asyncpg는 `ssl=true` 거부, sslmode enum만 허용)

### 3.3 포트 오버라이드 — `/home/ubuntu/pigos/docker-compose.deploy.yml`
기존 서버 포트(3000 dawoon, 3001 topic-lab, 8000 pigsignal)와 충돌 회피:
```yaml
services:
  web:
    ports: ["127.0.0.1:3010:3000"]
  api:
    ports: ["127.0.0.1:8010:8000"]
```

### 3.4 빌드 & 기동 (nginx 서비스 제외)
```bash
cd /home/ubuntu/pigos
sudo docker compose -f docker-compose.prod.yml -f docker-compose.deploy.yml up -d --build web api worker redis
```
> `ubuntu`는 docker 그룹 미적용 → `sudo` 필요. compose는 `docker-compose-v2` apt 패키지.

### 3.5 검증 (공개 노출 전)
```bash
curl 127.0.0.1:8010/health         # {"status":"ok"}
curl -o /dev/null -w '%{http_code}' 127.0.0.1:3010/onboarding   # 200
```

## 4. nginx vhost + 인증서

`/etc/nginx/sites-available/pigos-app` (app→3010, api→8010), `sites-enabled`에 심볼릭 링크.
HTTP 블록만 먼저 두고:
```bash
sudo nginx -t && sudo systemctl reload nginx     # restart 아님 — 무중단
sudo certbot --nginx -d app.pigos.io -d api.pigos.io \
  --non-interactive --agree-tos -m jhbae@wiselake.co.kr --redirect
```
> certbot이 443 + HTTP→HTTPS 리다이렉트를 자동 추가. 갱신은 `certbot.timer`로 자동.
> **AWS ACM 불가** (EC2 직접 nginx 구조 → ACM은 ALB/CloudFront 전용). Let's Encrypt가 정답.

## 5. 재배포 (코드 갱신 시)
```bash
# 1. 로컬 빌드/전송 (3.1) → 2. 컨테이너 재빌드
cd /home/ubuntu/pigos
sudo docker compose -f docker-compose.prod.yml -f docker-compose.deploy.yml up -d --build web api worker redis
```
랜딩만 갱신: 로컬 `npm run build` → `dist/` tar → scp → `/home/ubuntu/pigos-landing/dist` 교체 → `pm2 restart pigos-landing`.

## 6. 롤백
- 앱: `sudo docker compose ... down` (또는 이전 이미지로 `up`)
- nginx: `sudo rm /etc/nginx/sites-enabled/pigos-app && sudo systemctl reload nginx`
- 랜딩: `dist.bak.<timestamp>` 백업으로 복구

## 7. 복원력 / 운영
- 모든 컨테이너 `restart: unless-stopped` + `docker.service enabled` → **재부팅 자동 복구**
- 인증서: `certbot.timer` active → 자동 갱신
- 마이그레이션: API는 부팅 시 자동 마이그레이션을 **하지 않음** (alembic 수동). Supabase 스키마는 별도 관리.

## 8. 알려진 항목 / TODO
- [ ] **서버 GitHub deploy key 미설정** → 현재 scp 배포. 설정 시 서버에서 `git pull` 배포 가능:
  ```bash
  ssh-keygen -t ed25519 -f ~/.ssh/pigos_deploy -N "" -C "ec2-pigos-deploy"
  cat ~/.ssh/pigos_deploy.pub   # → GitHub pig-os → Settings → Deploy keys (read-only)
  ```
- [ ] **이중화 없음** (단일 EC2 = SPOF). 트래픽 증가 시 ALB + 다중 AZ 고려.
- [x] worker 헬스체크: api Dockerfile의 `/health` 상속으로 false unhealthy → compose에서 `healthcheck.disable: true` 처리됨.
