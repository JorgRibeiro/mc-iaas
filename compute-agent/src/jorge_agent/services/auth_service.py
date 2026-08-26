import secrets

from fastapi import (
    Header,
    HTTPException,
    WebSocket,
    WebSocketException,
    status,
)

from jorge_agent.config import PATHS


def _load_api_token() -> str:
    token_path = PATHS.agent_api_token_file

    if not token_path.exists():
        raise RuntimeError(
            f"Agent API token not found: {token_path}"
        )

    token = token_path.read_text(
        encoding="utf-8",
    ).strip()

    if not token:
        raise RuntimeError(
            "Agent API token is empty"
        )

    return token


def _extract_bearer_token(
    authorization: str | None,
) -> str:
    if authorization is None:
        raise ValueError(
            "Missing authorization token"
        )

    scheme, separator, token = (
        authorization.partition(" ")
    )

    if (
        not separator
        or scheme.lower() != "bearer"
        or not token
    ):
        raise ValueError(
            "Invalid authorization header"
        )

    return token


def _validate_api_token(
    authorization: str | None,
) -> None:
    provided_token = _extract_bearer_token(
        authorization
    )

    expected_token = _load_api_token()

    if not secrets.compare_digest(
        provided_token,
        expected_token,
    ):
        raise ValueError(
            "Invalid authorization token"
        )


def require_api_token(
    authorization: str | None = Header(
        default=None,
    ),
) -> None:
    try:
        _validate_api_token(
            authorization
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent authentication unavailable",
        ) from exc


def require_websocket_api_token(
    websocket: WebSocket,
) -> None:
    authorization = websocket.headers.get(
        "authorization"
    )

    try:
        _validate_api_token(
            authorization
        )

    except ValueError as exc:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise WebSocketException(
            code=status.WS_1011_INTERNAL_ERROR,
            reason="Agent authentication unavailable",
        ) from exc