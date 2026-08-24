# 프로덕션 롤백 런북

> 2026-08-24 장애 후 작성. 그날 되돌릴 수단이 없어 전진 수정밖에 못 했다.
> **당황하면 순서를 건너뛴다. 위에서부터 읽는다.**

---

## 0. 먼저 판단 — 무엇이 깨졌나

| 증상 | 원인 계층 | 가야 할 절차 |
|---|---|---|
| 502 / 접속 불가 | 컨테이너·포트 매핑 | **A** |
| 응답은 오는데 매우 느림 | DB 커넥션 풀러 | **B** |
| 기능이 잘못 동작 / 데이터가 이상 | 코드 | **C** |
| 스키마가 잘못 바뀜 | 마이그레이션 | **D** |
| 데이터가 손상·소실 | DB | **E** |

**A~C 는 되돌리기 쉽다. D·E 는 신중하게.**

---

## A. 502 · 접속 불가

거의 항상 **compose 파일 하나만 써서 포트 매핑이 빠진 것**이다.

```bash
sudo docker port pigos-api        # 8000/tcp -> 127.0.0.1:8010 이 나와야 정상
```

안 나오면:

```bash
cd ~/pigos
sudo docker compose -f docker-compose.prod.yml -f docker-compose.deploy.yml up -d api web
```

> `docker-compose.prod.yml` 단독으로 `up -d` 하면 `127.0.0.1:8010:8000` 매핑이 없어져
> 호스트 nginx 가 502 를 낸다. **항상 두 파일.**

---

## B. 매우 느림 (수십 초)

먼저 쿼리가 느린지, 커넥션이 느린지 가른다.

```bash
# 같은 요청을 5번 — 뒤로 갈수록 빨라지면 커넥션 문제다
for i in 1 2 3 4 5; do
  curl -s -o /dev/null -w "%{time_total}s\n" --max-time 60 https://api.pigos.io/health
done
```

**뒤로 갈수록 빨라진다 → 커넥션 수립 문제.** Supavisor 세션 슬롯이 묵은 세션으로 막힌 것이다.

```
해결: Supabase 대시보드 → Settings → Infrastructure → Restart project
      (약 1분 다운타임. Nano 컴퓨트라 그 정도 걸린다)
```

★ **api 를 반복 재기동하지 말 것.** 재기동마다 커넥션을 8개 새로 맺어야 해서 직후가 가장 느리다. 2026-08-24 에 그렇게 악화시켰다.

한도 실측:

```bash
sudo docker exec -i pigos-api python - <<'PY'
import asyncio, os, asyncpg
url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg://','postgresql://').split('?')[0]
async def m():
    held=[]
    for i in range(40):
        try: held.append(await asyncio.wait_for(asyncpg.connect(url, ssl='require'), timeout=20))
        except Exception as e: print(i, str(e)[:90]); break
    print('확보', len(held))
    for c in held: await c.close()
asyncio.run(m())
PY
```

---

## C. 코드 롤백 (가장 흔함)

```bash
sudo docker images | grep rollback          # 사용 가능한 시점 확인
```

`ops/deploy.sh` 로 배포했으면 `pigos-<svc>:rollback-<타임스탬프>` 가 최근 3개 남아 있다.

```bash
cd ~/pigos
TS=20260824-051600                          # 되돌릴 시점
sudo docker tag pigos-api:rollback-$TS pigos-api:latest
sudo docker tag pigos-web:rollback-$TS pigos-web:latest
sudo docker compose -f docker-compose.prod.yml -f docker-compose.deploy.yml up -d --no-build api web
curl -s -o /dev/null -w "%{http_code}\n" https://api.pigos.io/health
```

> `--no-build` 가 중요하다. 빼면 새 소스로 다시 빌드해서 롤백이 무효가 된다.

**롤백 태그가 없으면** 이 경로는 못 쓴다. 소스를 이전 커밋으로 되돌려 재빌드해야 한다(느리다).

---

## D. 마이그레이션 롤백

```bash
M="sudo docker run --rm --env-file ~/pigos/.env -v ~/mig-staging:/app -w /app pigos-api alembic"
$M current                    # 지금 어디인지
$M downgrade <되돌릴_리비전>
$M current                    # 확인
```

⚠️ **주의**

- `downgrade` 는 데이터를 지울 수 있다. 컬럼·테이블 drop 이 있으면 그 데이터는 사라진다.
- 코드가 새 스키마를 기대하는 상태에서 스키마만 되돌리면 앱이 깨진다. **C(코드 롤백)를 먼저 하고 D 를 한다.**
- 풀러 상태가 나쁘면 `ECHECKOUTTIMEOUT` 으로 실패한다. **락 문제가 아니므로 그냥 재시도**하면 붙는다.
- 실패는 트랜잭션째 롤백되니 중간 상태로 남지 않는다.

★ 실패 판정을 **풀러가 밀린 상태의 조회 결과로 내리지 말 것.** 2026-08-24 에 그 오판으로
이미 head 인 마커를 `stamp` 로 되돌려 `DuplicateTable` 사고를 만들었다.

---

## E. DB 복원 (최후 수단)

### E-1. Supabase 자체 백업 (1차)

대시보드 `Database → Backups` → 복원 지점 선택. **egress 비용이 없고 가장 빠르다.**

### E-2. 독립 덤프 (2차)

```bash
ls -lh ~/pigos-backups/                     # deploy 태그 붙은 게 배포 직전 스냅샷
```

```bash
# ⚠️ 복원은 기존 데이터를 덮어쓴다. 반드시 현재 상태를 먼저 뜬다.
~/pigos/ops/backup_db.sh full before-restore

URL=$(grep -E '^DATABASE_URL=' ~/pigos/.env | cut -d= -f2- | tr -d '"')
PGURL=$(printf '%s' "$URL" | sed -E 's#\+asyncpg##; s#\?ssl=require#?sslmode=require#')
gzip -dc ~/pigos-backups/pigos-full-<타임스탬프>-deploy.sql.gz | psql "$PGURL"
```

복원 후 반드시 확인:

```bash
$M current                                   # 마커가 덤프 시점과 맞는지
curl -s -o /dev/null -w "%{http_code}\n" https://api.pigos.io/health
```

---

## 사고 후 할 일

1. 무엇이 원인이었는지 **한 줄로** 적는다
2. 같은 일이 다시 나지 않게 하는 **테스트나 게이트**를 하나 추가한다
3. 이 문서에 증상 → 절차를 추가한다

> 2026-08-24 사례: 풀러 세션 포화로 커넥션 수립이 4~6초 → 대시보드 31초.
> 재기동을 반복해 악화. 교훈은 위 **B** 에 반영했다.
