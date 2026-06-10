#!/bin/bash
# PigOS EC2 초기 설정 스크립트 (ubuntu@52.78.65.6)
# 실행: bash setup.sh

set -e

echo "=== Docker 설치 ==="
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker ubuntu
echo "Docker 설치 완료"

echo "=== Certbot 설치 ==="
sudo apt-get install -y certbot
echo "Certbot 설치 완료"

echo "=== 코드 클론 ==="
cd /home/ubuntu
git clone git@github.com:foes88/pig-os.git pigos || (cd pigos && git pull)

echo "=== .env 파일 생성 (직접 편집 필요) ==="
cat > /home/ubuntu/pigos/.env.prod << 'EOF'
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_SUPABASE_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
REDIS_URL=redis://redis:6379/0
SECRET_KEY=CHANGE_THIS_TO_RANDOM_64_CHAR_STRING
EOF
echo ".env.prod 생성 완료 — SECRET_KEY 반드시 변경하세요!"

echo "=== SSL 인증서 발급 (DNS A 레코드 먼저 설정 필요) ==="
echo "아래 명령어를 DNS 설정 후 실행하세요:"
echo "  sudo certbot certonly --standalone -d app.pigos.io -d api.pigos.io --email jhbae@wiselake.co.kr --agree-tos"

echo "=== 완료 ==="
echo "다음 단계:"
echo "1. 가비아 DNS: A 레코드 app.pigos.io → 52.78.65.6"
echo "2. 가비아 DNS: A 레코드 api.pigos.io → 52.78.65.6"
echo "3. sudo certbot certonly --standalone -d app.pigos.io -d api.pigos.io"
echo "4. cd /home/ubuntu/pigos && docker compose -f docker-compose.prod.yml up -d"
