"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.api.router import api_router
from app.clients.compute_agent import ComputeAgentClient
from app.core.config import get_settings
from app.db.session import async_session_factory, engine
from app.secrets.environment import EnvironmentSecretProvider
from app.workers.node_poller import NodePoller
from app.workers.operation_runner import OperationRunner


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Own the shared Agent HTTP pool and database engine lifecycle."""
    settings = get_settings()
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                settings.agent_read_timeout, connect=settings.agent_connect_timeout
            ),
            trust_env=False,
            follow_redirects=False,
        ) as http_client:
            application.state.agent_client = ComputeAgentClient(http_client)
            application.state.secret_provider = EnvironmentSecretProvider()
            poller = NodePoller(
                async_session_factory,
                application.state.agent_client,
                application.state.secret_provider,
                settings,
            )
            application.state.node_poller = poller
            runner = OperationRunner(
                async_session_factory,
                application.state.agent_client,
                application.state.secret_provider,
            )
            application.state.operation_runner = runner
            poller.start()
            runner.start()
            try:
                yield
            finally:
                try:
                    await runner.stop()
                finally:
                    await poller.stop()
    finally:
        await engine.dispose()


app = FastAPI(
    title="MC-IaaS Control Plane",
    description="Control Plane API for the MC-IaaS distributed infrastructure platform",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(api_router)
