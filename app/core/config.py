from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ai-agent-workflows"
    app_version: str = "1.0.0"
    database_url: str = "sqlite+aiosqlite:///./data/workflows.db"
    max_tokens_per_ticket: int = 2000
    confidence_threshold: float = 0.75


settings = Settings()
