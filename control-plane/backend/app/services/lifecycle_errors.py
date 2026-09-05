"""Safe lifecycle errors independent of HTTP."""


class LifecycleError(Exception):
    message = "Instance lifecycle conflict"

    def __init__(self) -> None:
        super().__init__(self.message)


class InstanceNotFoundError(LifecycleError):
    message = "Instance not found"


class OperationNotFoundError(LifecycleError):
    message = "Operation not found"


class InstanceAlreadyExistsError(LifecycleError):
    message = "Instance name already reserved"


class ActiveOperationError(LifecycleError):
    message = "Instance has an active or uncertain operation"


class NoSchedulableNodeError(LifecycleError):
    message = "No schedulable Node"


class NodeNotUsableError(LifecycleError):
    message = "Assigned Node is not ready or its observation is stale"


class NodeCapacityError(LifecycleError):
    message = "Assigned Node has no available runtime slots"
