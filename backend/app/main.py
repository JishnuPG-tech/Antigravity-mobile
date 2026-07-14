try:
    from fastapi import FastAPI
    from backend.app.api import router as api_router

    app = FastAPI(title="Antigravity Bridge")
    app.include_router(api_router, prefix="/api")
except Exception:
    # FastAPI may not be installed in lightweight test environments.
    app = None

from backend.app.handlers import healthz

