"""Minimal contract for resolving Agent credentials."""

from typing import Protocol


class SecretProvider(Protocol):
    def get_agent_token(self, credential_ref: str) -> str: ...
