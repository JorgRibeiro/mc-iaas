"""Credential resolution from dotenv/environment, with safe errors."""

import pytest

from app.clients.errors import AgentCredentialUnavailableError
from app.secrets.environment import EnvironmentSecretProvider


@pytest.mark.parametrize("reference", ["jorge-agent", "JORGE_AGENT", "Jorge-Agent"])
def test_environment_reference(monkeypatch, tmp_path, reference):
    monkeypatch.setenv("MC_IAAS_AGENT_TOKEN_JORGE_AGENT", " test-token ")
    provider = EnvironmentSecretProvider(tmp_path / "missing")
    assert provider.get_agent_token(reference) == "test-token"


def test_dotenv_and_environment_precedence(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text('MC_IAAS_AGENT_TOKEN_TEST_AGENT="file-token"\n')
    monkeypatch.delenv("MC_IAAS_AGENT_TOKEN_TEST_AGENT", raising=False)
    provider = EnvironmentSecretProvider(path)
    assert provider.get_agent_token("test-agent") == "file-token"
    monkeypatch.setenv("MC_IAAS_AGENT_TOKEN_TEST_AGENT", "environment-token")
    assert provider.get_agent_token("test-agent") == "environment-token"
    monkeypatch.setenv("MC_IAAS_AGENT_TOKEN_TEST_AGENT", "")
    with pytest.raises(AgentCredentialUnavailableError):
        provider.get_agent_token("test-agent")
    assert "file-token" not in repr(provider)


@pytest.mark.parametrize("value", [None, "", "  ", "bad\ntoken", "bad token", "é"])
def test_missing_or_invalid_secret_is_safe(monkeypatch, tmp_path, value):
    if value is None:
        monkeypatch.delenv("MC_IAAS_AGENT_TOKEN_TEST_AGENT", raising=False)
    else:
        monkeypatch.setenv("MC_IAAS_AGENT_TOKEN_TEST_AGENT", value)
    with pytest.raises(AgentCredentialUnavailableError) as caught:
        EnvironmentSecretProvider(tmp_path / "missing").get_agent_token("test-agent")
    assert str(caught.value) == "Agent credential unavailable or invalid"


def test_invalid_reference_is_safe(tmp_path):
    with pytest.raises(AgentCredentialUnavailableError) as caught:
        EnvironmentSecretProvider(tmp_path / "missing").get_agent_token("sensitive/reference")
    assert "sensitive" not in str(caught.value)
