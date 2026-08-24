from fastapi import FastAPI, HTTPException
from fastapi import FastAPI, HTTPException, status
from jorge_agent.services.instance_service import (
    create_instance, 
    start_instance,
    stop_instance,
    restart_instance,
    delete_instance,
)

from jorge_agent.services.libvirt_service import (
    get_hypervisor_status,
    list_instances,
    get_instance,
)

from jorge_agent.services.metrics_service import (
    get_instance_metrics,
)

from jorge_agent.services.health_service import (
    get_instance_health,
)

from jorge_agent.schemas.instance import (
    InstanceCreate,
    InstanceCreateResponse,
    InstanceActionResponse,
    InstanceDeleteResponse,
    InstanceDetailResponse,
    InstanceMetricsResponse,
    InstanceHealthResponse,
    InstanceSummaryResponse,
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


@app.get(
    "/instances",
    response_model=list[InstanceSummaryResponse],
)
def get_instances() -> list[InstanceSummaryResponse]:
    try:
        return list_instances()

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to list instances: {exc}",
        ) from exc


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

@app.delete(
    "/instances/{name}",
    response_model=InstanceDeleteResponse,
)
def delete_instance_endpoint(
    name: str,
    delete_data: bool = False,
) -> InstanceDeleteResponse:
    try:
        return delete_instance(
            name=name,
            delete_data=delete_data,
        )

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

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Instance deletion failed: {exc}",
        ) from exc

@app.get(
    "/instances/{name}",
    response_model=InstanceDetailResponse,
)
def get_instance_endpoint(
    name: str,
) -> InstanceDetailResponse:
    try:
        return get_instance(name)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not get instance: {exc}",
        ) from exc

@app.get(
    "/instances/{name}/metrics",
    response_model=InstanceMetricsResponse,
)
def get_instance_metrics_endpoint(
    name: str,
) -> InstanceMetricsResponse:
    try:
        return get_instance_metrics(name)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not get metrics: {exc}",
        ) from exc

@app.get(
    "/instances/{name}/health",
    response_model=InstanceHealthResponse,
)
def get_instance_health_endpoint(
    name: str,
) -> InstanceHealthResponse:
    try:
        return get_instance_health(name)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not get instance health: {exc}",
        ) from exc