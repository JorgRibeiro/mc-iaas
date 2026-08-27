from datetime import datetime

from pydantic import BaseModel


class AgentStatusResponse(BaseModel):
    status: str
    service: str
    version: str
    started_at: datetime
    uptime_seconds: float
