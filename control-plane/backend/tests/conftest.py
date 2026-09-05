"""Shared test environment configuration."""

import os
from unittest.mock import AsyncMock, Mock

import pytest

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://mc_iaas:development-only@127.0.0.1:5432/mc_iaas",
)


@pytest.fixture(autouse=True)
def lifespan_poller(monkeypatch):
    """API unit tests must never start real polling against local Nodes."""
    from app import main

    poller = Mock()
    poller.stop = AsyncMock()
    monkeypatch.setattr(main, "NodePoller", Mock(return_value=poller))
    runner = Mock()
    runner.stop = AsyncMock()
    monkeypatch.setattr(main, "OperationRunner", Mock(return_value=runner))
    return poller
