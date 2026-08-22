from fastapi import FastAPI, HTTPException

from jorge_agent.services.libvirt_service import get_hypervisor_status

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