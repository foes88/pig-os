# 비밀번호 재설정 — 초안 (DRAFT, 미적용)

> 상태: **초안.** 라이브 코드/DB 미반영. 적용하려면 §6 체크리스트 순서대로.
> 작성 2026-06-25. 현재 앱은 비번찾기를 "관리자 문의" 안내 다이얼로그로 처리(백엔드 엔드포인트 부재).
> 선결 결정 1개: **이메일(또는 SMS) 전송 수단** — 이게 없으면 토큰을 사용자에게 전달할 길이 없음(§5).

---

## 1. 흐름

```
[사용자] 비번 찾기 → 이메일 입력
   │  POST /auth/password-reset/request { email }
   ▼
[서버] 사용자 존재·active면 → 1회용 토큰 생성, 해시 저장(TTL 30분), 이메일로 링크 전송
        (존재 여부와 무관하게 항상 204 — 계정 열거(enumeration) 방지)
   ▼
[사용자] 메일의 링크/코드로 새 비번 입력
   │  POST /auth/password-reset/confirm { token, new_password }
   ▼
[서버] 토큰 검증(해시일치·미만료·미사용) → password_hash 갱신
        → 토큰 used 처리 + 해당 유저 refresh_token 전부 폐기(강제 재로그인)
```

## 2. API 계약

### POST /api/v1/auth/password-reset/request
- body: `{ "email": "user@farm.com" }`
- res: **204 No Content** (항상 — 계정 존재 여부 노출 금지)
- 부수효과: 유저 존재+active면 reset 토큰 생성·전송. rate-limit 권장(이메일당 분당 1~2회).

### POST /api/v1/auth/password-reset/confirm
- body: `{ "token": "<urlsafe>", "new_password": "..." }`
- res: **204** 성공 / **400** 토큰 무효·만료·사용됨 / **422** 비번 정책 위반
- 부수효과: password_hash 갱신, 토큰 used_at 기록, 유저 refresh_token 전부 삭제.

## 3. 토큰 전략 (RefreshToken 패턴 미러)
- 원문 토큰 = `secrets.token_urlsafe(32)` (사용자에게만 전달, DB엔 저장 안 함).
- DB엔 **해시만** 저장(`sha256`) — RefreshToken.token_hash와 동일 사상.
- TTL 30분, **1회용**(used_at), 사용 시 즉시 무효.
- confirm 시 해당 유저의 **다른 미사용 reset 토큰도 전부 무효**(재발급 시 이전 링크 폐기).

## 4. 레퍼런스 구현 (적용 시 그대로 사용)

### 4-1. 모델 — `app/db/models/platform.py` 에 추가
```python
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # sha256 hex
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

### 4-2. 마이그레이션 — `alembic revision -m "password_reset_tokens"`
```python
def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_prt_user", "password_reset_tokens", ["user_id"])

def downgrade() -> None:
    op.drop_table("password_reset_tokens")
```

### 4-3. 스키마 — `app/schemas/auth.py` 에 추가
```python
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
```

### 4-4. 서비스 — `app/services/auth_service.py` 에 추가
```python
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

RESET_TTL = timedelta(minutes=30)

def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

async def request_password_reset(db: AsyncSession, email: str) -> str | None:
    """유저 있으면 (원문토큰) 반환 — 호출부가 이메일 전송. 없으면 None(열거 방지: 라우터는 항상 204)."""
    user = await db.scalar(select(User).where(User.email == email, User.active.is_(True)))
    if not user:
        return None
    raw = secrets.token_urlsafe(32)
    db.add(PasswordResetToken(
        user_id=user.id, token_hash=_hash_token(raw),
        expires_at=datetime.now(UTC) + RESET_TTL,
    ))
    await db.flush()
    return raw

async def confirm_password_reset(db: AsyncSession, token: str, new_password: str) -> None:
    prt = await db.scalar(select(PasswordResetToken).where(
        PasswordResetToken.token_hash == _hash_token(token)))
    now = datetime.now(UTC)
    if not prt or prt.used_at is not None or prt.expires_at < now:
        raise ValidationError("토큰이 유효하지 않거나 만료되었습니다.")  # 라우터에서 400
    user = await db.get(User, prt.user_id)
    if not user:
        raise ValidationError("토큰이 유효하지 않습니다.")
    user.password_hash = hash_password(new_password)
    prt.used_at = now
    # 같은 유저의 다른 미사용 토큰 폐기 + refresh 토큰 전부 삭제(강제 재로그인)
    await db.execute(update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
        .values(used_at=now))
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await db.flush()
```

### 4-5. 라우터 — `app/routers/base/auth.py` 에 추가
```python
@router.post("/password-reset/request", status_code=204)
async def password_reset_request(body: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    raw = await auth_service.request_password_reset(db, body.email)
    if raw:
        await send_reset_email(body.email, raw)   # §5 — 전송 수단 필요
    await db.commit()
    return Response(status_code=204)              # 항상 204(열거 방지)

@router.post("/password-reset/confirm", status_code=204)
async def password_reset_confirm(body: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    await auth_service.confirm_password_reset(db, body.token, body.new_password)
    await db.commit()
    return Response(status_code=204)
```

## 5. ⚠️ 선결 결정 — 토큰 전달 수단 (이게 핵심 미싱)
`send_reset_email`이 없으면 토큰을 사용자에게 전달할 길이 없다. 택1 필요:
- **SMTP/SendGrid/AWS SES** — 표준. 발신 도메인·API키 필요.
- **SMS(베트남/태국 등)** — 이메일 미보급 시장 고려.
- **운영자 중개(interim)** — 토큰을 운영자 콘솔에 노출, 운영자가 전달. 가장 빠른 임시안.
- 결정 전까지 confirm 흐름만 테스트하려면: 개발용으로 request가 토큰을 **응답/로그에 노출**(운영 절대 금지, `settings.debug` 게이트).

## 6. 적용 체크리스트 (초안 → 실배포)
1. [ ] §5 토큰 전달 수단 결정 + `send_reset_email` 구현
2. [ ] 4-1 모델 + 4-2 마이그레이션 추가 → `alembic upgrade head`
3. [ ] 4-3/4-4/4-5 스키마·서비스·라우터 반영(import: `update`, `delete`, `Response`, `EmailStr`)
4. [ ] 테스트: 요청 204(존재/부재 모두)·confirm 성공·만료·재사용·refresh 폐기 확인
5. [ ] rate-limit(요청 엔드포인트) + 비번 정책 정합
6. [ ] 앱: 안내 다이얼로그 → 재설정 요청 화면 + (딥링크) confirm 화면. Android·iOS 동형.

## 7. 앱(클라) 초안 메모
- Android: `LoginScreen`의 비번찾기 다이얼로그 → 이메일 입력 시트(`POST request` → "메일을 확인하세요" 안내). confirm은 메일 딥링크(`pigos://reset?token=...`) → 새 비번 화면.
- iOS: 동일 흐름(String Catalog). 빌드검증 Mac.
- 7개 언어 문자열 필요(en/ko/zh/es/vi/th/pt).
