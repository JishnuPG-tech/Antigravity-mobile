from contextlib import asynccontextmanager
from backend.app.handlers import healthz
from bot.telegram_bot import run_bot_async, stop_bot_async
from core.state_store import init_db, close_db


@asynccontextmanager
async def lifespan(app):
    import asyncio
    # Initialize persistent state database
    await init_db()
    # Start Telegram Bot in the background using FastAPI's event loop
    bot_task = asyncio.create_task(run_bot_async())
    yield
    # Stop Telegram Bot gracefully
    await stop_bot_async()
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass
    await close_db()


try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    from backend.app.api import router as api_router
    from backend.app.webapp_html import HTML_CONTENT

    app = FastAPI(title="Antigravity Bridge", lifespan=lifespan)
    app.include_router(api_router, prefix="/api")

    @app.api_route("/", methods=["GET", "HEAD"])
    async def root():
        return {
            "status": "ok",
            "service": "Antigravity Bridge",
            "routes": ["/healthz", "/docs", "/api/sessions/new", "/webapp"],
        }

    @app.get("/webapp", response_class=HTMLResponse)
    async def get_webapp():
        return HTML_CONTENT

    @app.api_route("/healthz", methods=["GET", "HEAD"])
    async def health():
        return await healthz()

except Exception:
    # FastAPI may not be installed in lightweight test environments.
    app = None
