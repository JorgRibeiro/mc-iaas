"""Agent HTTP adapter using the application's shared connection pool."""

import logging
from urllib.parse import quote

import httpx
from pydantic import ValidationError

from app.clients.errors import (
    AgentAuthenticationError,
    AgentConflictError,
    AgentError,
    AgentNotFoundError,
    AgentResponseError,
    AgentTimeoutError,
    AgentUnavailableError,
    AgentValidationError,
)
from app.schemas.agent import AgentActionResult, AgentDeleteResult, AgentSnapshot
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

    async def _mutate(
        self,
        endpoint: str,
        token: str,
        method: str,
        path: str,
        *,
        payload: dict | None = None,
        delete: bool = False,
    ) -> AgentActionResult | AgentDeleteResult:
        try:
            base = normalize_endpoint(endpoint)
        except ValueError:
            raise AgentResponseError() from None
        try:
            response = await self._http_client.request(
                method,
                base + path,
                headers={"Authorization": "Bearer " + token},
                json=payload,
                params={"delete_data": "false"} if delete else None,
                follow_redirects=False,
            )
        except httpx.TimeoutException:
            raise AgentTimeoutError() from None
        except httpx.RequestError:
            raise AgentUnavailableError() from None
        known = {
            401: AgentAuthenticationError,
            403: AgentAuthenticationError,
            404: AgentNotFoundError,
            409: AgentConflictError,
            400: AgentValidationError,
            422: AgentValidationError,
        }
        if response.status_code in known:
            raise known[response.status_code]()
        if response.status_code == 504:
            raise AgentTimeoutError()
        if not response.is_success:
            raise AgentResponseError()
        try:
            schema = AgentDeleteResult if delete else AgentActionResult
            # Extra fields, including generated_password, are discarded immediately.
            return schema.model_validate_json(response.content)
        except ValidationError:
            raise AgentResponseError() from None

    async def create_instance(self, endpoint: str, token: str, payload: dict):
        return await self._mutate(endpoint, token, "POST", "/instances", payload=payload)

    async def start_instance(self, endpoint: str, token: str, name: str):
        return await self._mutate(
            endpoint, token, "POST", f"/instances/{quote(name, safe='')}/start"
        )

    async def stop_instance(self, endpoint: str, token: str, name: str):
        return await self._mutate(
            endpoint, token, "POST", f"/instances/{quote(name, safe='')}/stop"
        )

    async def restart_instance(self, endpoint: str, token: str, name: str):
        return await self._mutate(
            endpoint, token, "POST", f"/instances/{quote(name, safe='')}/restart"
        )

    async def delete_instance(self, endpoint: str, token: str, name: str):
        return await self._mutate(
            endpoint, token, "DELETE", f"/instances/{quote(name, safe='')}", delete=True
        )
