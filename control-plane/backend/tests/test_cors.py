"""Only configured local frontend origins may access the development API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.parametrize("origin", ["http://localhost:8080", "http://127.0.0.1:8080"])
def test_local_cors_preflight(origin):
    with TestClient(app) as client:
        response = client.options("/api/v1/instances", headers={
            "Origin": origin, "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "access-control-allow-credentials" not in response.headers


def test_unconfigured_origin_not_allowed():
    with TestClient(app) as client:
        response = client.options("/api/v1/instances", headers={
            "Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST",
        })
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
