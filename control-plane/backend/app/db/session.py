"""Asynchronous SQLAlchemy engine and session factory."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def check_database_connectivity() -> None:
    """Raise an exception when a simple PostgreSQL query cannot complete."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
