import os
from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(StrEnum):
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    app_env: AppEnvironment
    # Fallback connection string, used only when the discovery endpoint is
    # unreachable or returns a bad response. The prod DB URL changes over
    # time, so the endpoint is always the primary source.
    database_url: str | None = None
    # Credentials used when the discovery endpoint returns a bare tunnel URL
    # (tcp://host:port) that carries no user/password/database.
    database_user: str = "postgres"
    database_password: str = "postgres"
    database_name: str = "postgres"
    database_url_endpoint: str = "http://localhost:8000/db-url"
    database_url_endpoint_key: str | None = "dev-key"
    worker_api_key: str | None = None
    debug: bool = False
    database_url_timeout_seconds: float = 5.0

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_test(self) -> bool:
        return self.app_env == AppEnvironment.TEST


@lru_cache
def get_settings() -> Settings:
    return Settings()
