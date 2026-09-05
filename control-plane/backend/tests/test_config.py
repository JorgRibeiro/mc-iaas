"""Tests for application settings."""

from app.core.config import Settings


def test_settings_load_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:password@db/example")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()  # type: ignore[call-arg]

    assert settings.database_url == "postgresql+asyncpg://user:password@db/example"
    assert settings.host == "127.0.0.1"
    assert settings.port == 9000
    assert settings.log_level == "DEBUG"


def test_polling_settings_validate_threshold_and_intervals():
    import pytest
    from pydantic import ValidationError

    for key, value in [
        ("NODE_OFFLINE_THRESHOLD", 0),
        ("NODE_OFFLINE_THRESHOLD", 1.5),
        ("NODE_POLL_INTERVAL", 0),
        ("NODE_MAX_BACKOFF", -1),
        ("NODE_POLL_INTERVAL", float("nan")),
        ("NODE_MAX_BACKOFF", float("inf")),
    ]:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, **{key: value})
