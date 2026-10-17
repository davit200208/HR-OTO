from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HR-OTO Server"
    app_env: str = "development"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://hr_oto:change_me@localhost:5432/hr_oto"
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"
    secret_storage_provider: str = "environment"
    jwt_secret_key: str = "change_me_in_production_use_32_chars_minimum"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 30
    password_reset_minutes: int = 30
    mfa_issuer: str = "HR-OTO"
    bootstrap_token: str = "change_me_local_bootstrap"
    central_database_url: str = ""
    database_admin_url: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

