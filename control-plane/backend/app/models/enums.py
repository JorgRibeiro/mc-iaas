"""Stable values persisted by the Control Plane domain models."""

from enum import StrEnum


class DomainEnum(StrEnum):
    """Base type for string-valued domain enums."""


class NodeReachability(DomainEnum):
    UNKNOWN = "unknown"
    ONLINE = "online"
    OFFLINE = "offline"


class NodeHealth(DomainEnum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DesiredInstanceState(DomainEnum):
    STOPPED = "stopped"
    RUNNING = "running"
    ABSENT = "absent"


class ObservedInstanceState(DomainEnum):
    UNKNOWN = "unknown"
    MISSING = "missing"
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class MinecraftStatus(DomainEnum):
    UNKNOWN = "unknown"
    ONLINE = "online"
    OFFLINE = "offline"
    UNAVAILABLE = "unavailable"


class OperationType(DomainEnum):
    CREATE = "create"
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    DELETE = "delete"
    RECONCILE = "reconcile"


class OperationStatus(DomainEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNCERTAIN = "uncertain"


class EventLevel(DomainEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
