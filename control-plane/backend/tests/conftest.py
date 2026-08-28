"""Shared test environment configuration."""

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://mc_iaas:development-only@127.0.0.1:5432/mc_iaas",
)
