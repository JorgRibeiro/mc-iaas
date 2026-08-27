from pydantic import BaseModel


class RecoveryResponse(BaseModel):
    recovered: list[str]
    unchanged: list[str]
    errors: dict[str, str]

    healthy: bool
