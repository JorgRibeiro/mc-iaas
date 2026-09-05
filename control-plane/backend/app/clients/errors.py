"""Safe semantic errors; never include transport details or remote payloads."""


class AgentError(Exception):
    message = "Agent request failed"

    def __init__(self) -> None:
        super().__init__(self.message)


class AgentUnavailableError(AgentError):
    message = "Agent unavailable"


class AgentTimeoutError(AgentError):
    message = "Agent request timed out"


class AgentAuthenticationError(AgentError):
    message = "Agent authentication failed"


class AgentResponseError(AgentError):
    message = "Invalid or unsuccessful Agent response"


class AgentCredentialUnavailableError(AgentError):
    message = "Agent credential unavailable or invalid"


class AgentNotFoundError(AgentError):
    message = "Agent workload not found"


class AgentConflictError(AgentError):
    message = "Agent rejected lifecycle or capacity conflict"


class AgentValidationError(AgentError):
    message = "Agent rejected workload parameters"
