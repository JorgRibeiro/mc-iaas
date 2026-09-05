"""Environment-backed application settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Control Plane configuration loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    control_plane_name: str = Field(
        default="MC-IaaS Control Plane", validation_alias="CONTROL_PLANE_NAME"
    )
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    host: str = Field(default="127.0.0.1", validation_alias="HOST")
    port: int = Field(default=8001, validation_alias="PORT")

    cors_origins: list[str] = Field(
        default=["http://localhost:8080", "http://127.0.0.1:8080"],
        validation_alias="CORS_ORIGINS",
    )

    database_url: str = Field(validation_alias="DATABASE_URL")

    agent_connect_timeout: float = Field(default=5.0, validation_alias="AGENT_CONNECT_TIMEOUT")
    agent_read_timeout: float = Field(default=30.0, validation_alias="AGENT_READ_TIMEOUT")

    node_observation_max_age: float = Field(
        default=60.0, gt=0, allow_inf_nan=False, validation_alias="NODE_OBSERVATION_MAX_AGE"
    )

    node_poll_interval: float = Field(
        default=10.0, gt=0, allow_inf_nan=False, validation_alias="NODE_POLL_INTERVAL"
    )
    node_offline_threshold: int = Field(default=30, ge=1, validation_alias="NODE_OFFLINE_THRESHOLD")
    node_max_backoff: float = Field(
        default=300.0, gt=0, allow_inf_nan=False, validation_alias="NODE_MAX_BACKOFF"
    )

    reconciliation_interval: float = Field(
        default=15.0, gt=0, allow_inf_nan=False, validation_alias="RECONCILIATION_INTERVAL"
    )
    reconciliation_retry_limit: int = Field(
        default=3, ge=0, validation_alias="RECONCILIATION_RETRY_LIMIT"
    )

    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()  # type: ignore[call-arg]
