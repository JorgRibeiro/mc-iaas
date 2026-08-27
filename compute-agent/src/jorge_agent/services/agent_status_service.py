import time

from datetime import (
    datetime,
    timezone,
)

from jorge_agent import __version__
from jorge_agent.schemas.agent import (
    AgentStatusResponse,
)


_STARTED_AT = datetime.now(
    timezone.utc
)

_STARTED_MONOTONIC = time.monotonic()


def get_agent_status() -> AgentStatusResponse:
    uptime_seconds = (
        time.monotonic()
        - _STARTED_MONOTONIC
    )

    return AgentStatusResponse(
        status="running",
        service="jorge-agent",
        version=__version__,
        started_at=_STARTED_AT,
        uptime_seconds=round(
            uptime_seconds,
            2,
        ),
    )
