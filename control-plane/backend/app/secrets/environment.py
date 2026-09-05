"""Resolve references from the process environment or a local dotenv file."""

import os
import re
from pathlib import Path

from dotenv import dotenv_values

from app.clients.errors import AgentCredentialUnavailableError


class EnvironmentSecretProvider:
    def __init__(self, env_file: str | Path = ".env") -> None:
        # Do not modify os.environ, interpolate values, or expose them through Settings.
        self._file_values = dotenv_values(env_file, interpolate=False)

    def get_agent_token(self, credential_ref: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", credential_ref):
            raise AgentCredentialUnavailableError()
        key = "MC_IAAS_AGENT_TOKEN_" + credential_ref.upper().replace("-", "_")
        value = os.environ.get(key, self._file_values.get(key))
        token = value.strip() if value else ""
        if not token or any(ord(character) < 33 or ord(character) > 126 for character in token):
            raise AgentCredentialUnavailableError()
        return token
