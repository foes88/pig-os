from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "postgresql+asyncpg://pigos:pigos@localhost:5432/pigos"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production-at-least-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    environment: str = "development"
    cors_origins: list[str] = [
        "https://pigos.io",
        "https://app.pigos.io",
        "https://admin.pigos.io",  # 운영자 콘솔 — 누락 시 admin API 호출 CORS 차단
    ]

    # Supabase (파일럿 신청용 + 프로덕션 DB)
    supabase_url: str = ""
    supabase_anon_key: str = ""

    # FCM 푸시 (G1) — 둘 다 설정돼야 푸시 전송, 아니면 graceful skip
    fcm_project_id: str = ""
    # 서비스 계정 JSON 경로 (google-auth가 읽음). 미설정 시 푸시 비활성.
    fcm_credentials_path: str = ""

    # SMTP 이메일 발송 (비밀번호 재설정 등). host+user+password 모두 설정돼야 전송, 아니면 graceful
    # skip(로그 폴백) — 비밀값은 env로만 주입(코드에 하드코딩 금지).
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""          # 발신 주소(미설정 시 smtp_user 사용)
    smtp_use_tls: bool = True    # 587 STARTTLS
    # 이메일 내 링크용 프론트 베이스 URL (예: https://app.pigos.io)
    app_base_url: str = "http://localhost:3000"

    # KPI Governance 3-table benchmark 연결 (handoff/KPI_GOVERNANCE_v3.1.md).
    # True: Rule Engine이 governance resolver만 사용(검증 안 된 benchmark는 발화 금지+insufficient).
    # False(기본): 기존 default_metric_values 경로 유지(롤백 전용·현행 동작). 운영 전환 전까지 False.
    use_governance_benchmarks: bool = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def smtp_configured(self) -> bool:
        """host+user+password 다 있어야 실제 발송. 하나라도 없으면 로그 폴백."""
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    @property
    def sync_database_url(self) -> str:
        """Alembic needs synchronous URL."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")


settings = Settings()
