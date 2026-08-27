from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_football_key: str = ""
    api_football_base_url: str = "https://v3.football.api-sports.io"
    database_url: str = "postgresql+psycopg://sports_bi:sports_bi@db:5432/sports_bi"
    redis_url: str = "redis://redis:6379/0"
    cors_origins: str = "*"
    api_timeout_seconds: float = 20.0
    api_max_retries: int = 3
    api_daily_request_limit: int = 100
    redis_cache_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()