from fastapi import FastAPI

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