from fastapi import FastAPI, HTTPException
from fastapi import FastAPI, HTTPException, status
from jorge_agent.services.instance_service import (
    create_instance, 
    start_instance,
    stop_instance,
    restart_instance,
)

from jorge_agent.services.libvirt_service import (
    get_hypervisor_status,
    list_instances,
)

from jorge_agent.schemas.instance import (
    InstanceCreate,
    InstanceCreateResponse,
    InstanceActionResponse
)


app = FastAPI(
    title="Jorge Agent",
    description="Compute Node Agent for MC-IaaS",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "jorge-agent",
    }


@app.get("/hypervisor/health")
def hypervisor_health():
    try:
        hypervisor = get_hypervisor_status()

        return {
            "status": "ok",
            "hypervisor": hypervisor,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Hypervisor unavailable: {exc}",
        )


@app.get("/instances")
def get_instances():
    try:
        return list_instances()

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to list instances: {exc}",
        )


@app.post(
    "/instances",
    response_model=InstanceCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_instance(
    instance: InstanceCreate,
) -> InstanceCreateResponse:
    try:
        return create_instance(instance)

    except FileExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Instance creation failed: {exc}",
        ) from exc

@app.post(
    "/instances/{name}/start",
    response_model=InstanceActionResponse,
)
def post_instance_start(
    name: str,
) -> InstanceActionResponse:
    try:
        return start_instance(name)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Instance start failed: {exc}",
        ) from exc

@app.post(
    "/instances/{name}/stop",
    response_model=InstanceActionResponse,
)
def post_instance_stop(
    name: str,
) -> InstanceActionResponse:
    try:
        return stop_instance(name)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Instance stop failed: {exc}",
        ) from exc

@app.post(
    "/instances/{name}/restart",
    response_model=InstanceActionResponse,
)
def post_instance_restart(
    name: str,
) -> InstanceActionResponse:
    try:
        return restart_instance(name)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Instance restart failed: {exc}",
        ) from exc