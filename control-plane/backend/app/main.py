"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.clients.compute_agent import ComputeAgentClient
from app.core.config import get_settings
from app.db.session import async_session_factory, engine
from app.secrets.environment import EnvironmentSecretProvider
from app.workers.node_poller import NodePoller
from app.workers.operation_runner import OperationRunner
from app.workers.reconciliation_loop import ReconciliationLoop


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
            reconciliation = ReconciliationLoop(async_session_factory, settings)
            application.state.reconciliation_loop = reconciliation
            poller.start()
            runner.start()
            reconciliation.start()
            try:
                yield
            finally:
                try:
                    try:
                        await reconciliation.stop()
                    finally:
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)
app.include_router(api_router)
