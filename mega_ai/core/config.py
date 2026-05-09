from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str
    e2b_api_key: str = ""

    postgres_user: str = "megaai"
    postgres_password: str = "megaai_secret"
    postgres_db: str = "megaai"

    database_url: str = "postgresql://megaai:megaai_secret@localhost:5432/megaai"

    log_level: str = "INFO"

    default_context_budget: int = 8000
    max_tool_retries: int = 2
    compression_threshold: float = 0.85

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()