import asyncio
from backend.app.main import healthz


def test_health():
    res = asyncio.run(healthz())
    assert res["status"] == "ok"
