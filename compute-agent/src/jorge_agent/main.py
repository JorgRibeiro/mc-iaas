import logging

from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
    APIRouter,
    Depends,
)

from jorge_agent.services.auth_service import (
    require_api_token,
    require_websocket_api_token,
)

from jorge_agent.services.console_bridge import (
    bridge_instance_console,
)

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
    MinecraftCommandRequest,
    MinecraftCommandResponse,
)

from jorge_agent.services.rcon_service import (
    RconError,
    execute_rcon_command,
)

from jorge_agent.services.minecraft_console_bridge import (
    bridge_minecraft_console,
)

from jorge_agent.services.invariant_service import (
    check_invariants,
)

from jorge_agent.services.recovery_service import (
    reconcile_instance_runtimes,
)

logger = logging.getLogger(
    "jorge_agent"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting compute node reconciliation"
    )

    recovery = (
        reconcile_instance_runtimes()
    )

    for name in recovery.recovered:
        logger.warning(
            "Recovered stale runtime: %s",
            name,
        )

    for name, error in recovery.errors.items():
        logger.error(
            "Runtime recovery failed for %s: %s",
            name,
            error,
        )

    if recovery.errors:
        raise RuntimeError(
            "Compute node runtime recovery failed"
        )

    invariants = check_invariants()

    if not invariants.healthy:
        details = "; ".join(
            (
                f"{issue.code}"
                + (
                    f"[{issue.instance}]"
                    if issue.instance
                    else ""
                )
                + f": {issue.detail}"
            )
            for issue in invariants.issues
        )

        raise RuntimeError(
            "Compute node invariants failed: "
            + details
        )

    logger.info(
        "Compute node reconciliation complete"
    )

    yield

app = FastAPI(
    title="Jorge Agent",
    description="Compute Node Agent for MC-IaaS",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

protected_api = APIRouter(
    dependencies=[
        Depends(require_api_token),
    ],
)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "jorge-agent",
    }


@protected_api.get("/hypervisor/health")
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


@protected_api.get(
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


@protected_api.post(
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

@protected_api.post(
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

@protected_api.post(
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

@protected_api.post(
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

@protected_api.delete(
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

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Instance deletion failed: {exc}",
        ) from exc

@protected_api.get(
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

@protected_api.get(
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

@protected_api.get(
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

@app.websocket(
    "/instances/{name}/console"
)
async def instance_console_websocket(
    websocket: WebSocket,
    name: str,
    _: None = Depends(
        require_websocket_api_token
    ),
) -> None:
    try:
        await bridge_instance_console(
            name,
            websocket,
        )

    except WebSocketDisconnect:
        pass

    except FileNotFoundError:
        await websocket.close(
            code=4404,
            reason="Instance not found",
        )

    except RuntimeError as exc:
        await websocket.close(
            code=4409,
            reason=str(exc),
        )

    except Exception:
        await websocket.close(
            code=1011,
            reason="Console internal error",
        )

@protected_api.post(
    "/instances/{name}/minecraft/command",
    response_model=MinecraftCommandResponse,
)
def minecraft_command(
    name: str,
    request: MinecraftCommandRequest,
) -> MinecraftCommandResponse:
    try:
        response = execute_rcon_command(
            name,
            request.command,
        )

        return MinecraftCommandResponse(
            name=name,
            command=request.command,
            response=response,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RconError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except OSError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"RCON unavailable: {exc}",
        )

@app.websocket(
    "/instances/{name}/minecraft/console"
)
async def minecraft_console_websocket(
    websocket: WebSocket,
    name: str,
    _: None = Depends(
        require_websocket_api_token
    ),
) -> None:
    try:
        await bridge_minecraft_console(
            name,
            websocket,
        )

    except WebSocketDisconnect:
        pass

    except Exception:
        try:
            await websocket.close(
                code=1011,
                reason="Minecraft console internal error",
            )
        except Exception:
            pass

