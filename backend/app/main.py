from backend.app.handlers import healthz

try:
    from fastapi import FastAPI
    from backend.app.api import router as api_router

    app = FastAPI(title="Antigravity Bridge")
    app.include_router(api_router, prefix="/api")

    @app.get("/")
    async def root():
        return {
            "status": "ok",
            "service": "Antigravity Bridge",
            "routes": ["/healthz", "/docs", "/api/sessions/new"],
        }

    @app.get("/healthz")
    async def health():
        return await healthz()
except Exception:
    # FastAPI may not be installed in lightweight test environments.
    app = None

