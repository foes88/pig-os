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

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def sync_database_url(self) -> str:
        """Alembic needs synchronous URL."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")


settings = Settings()
