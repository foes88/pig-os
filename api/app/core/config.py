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
    cors_origins: list[str] = ["https://pigos.io", "https://app.pigos.io"]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def sync_database_url(self) -> str:
        """Alembic needs synchronous URL."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")


settings = Settings()
