"""Read-only Agent HTTP adapter using the application's shared connection pool."""

import logging

import httpx
from pydantic import ValidationError

from app.clients.errors import (
    AgentAuthenticationError,
    AgentError,
    AgentResponseError,
    AgentTimeoutError,
    AgentUnavailableError,
)
from app.schemas.agent import AgentSnapshot
from app.schemas.node import normalize_endpoint

logger = logging.getLogger(__name__)


class ComputeAgentClient:
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http_client = http_client

    async def get_snapshot(self, endpoint: str, bearer_token: str) -> AgentSnapshot:
        try:
            try:
                base_url = normalize_endpoint(endpoint)
            except (ValueError, ValidationError):
                raise AgentResponseError() from None
            try:
                response = await self._http_client.get(
                    base_url + "/node/snapshot",
                    headers={"Authorization": "Bearer " + bearer_token},
                    follow_redirects=False,
                )
            except httpx.TimeoutException:
                raise AgentTimeoutError() from None
            except httpx.RequestError:
                raise AgentUnavailableError() from None
            if response.status_code in {401, 403}:
                raise AgentAuthenticationError()
            if not response.is_success:
                raise AgentResponseError()
            try:
                return AgentSnapshot.model_validate_json(response.content)
            except ValidationError:
                raise AgentResponseError() from None
        except AgentError as error:
            logger.warning("agent.request.failed error=%s", type(error).__name__)
            raise
