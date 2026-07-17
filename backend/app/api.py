import logging
import subprocess
import asyncio

from fastapi import APIRouter, Body, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from backend.app.config import settings
from core.session_manager import SessionManager
from bot.telegram_bot import clean_terminal_output
import httpx
import os

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateSessionReq(BaseModel):
    user_id: int
    project: str | None = "default"


class SendInputReq(BaseModel):
    user_id: int
    text: str


class InterruptReq(BaseModel):
    user_id: int


class SendKeyReq(BaseModel):
    user_id: int
    key: str


@router.post("/sessions/new")
async def new_session(req: CreateSessionReq):
    sm = SessionManager(settings)
    try:
        sm.ensure_session(str(req.user_id), project=req.project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "created"}


@router.post("/sessions/send")
async def send_input(req: SendInputReq):
    sm = SessionManager(settings)
    try:
        sm.send_input(str(req.user_id), req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "sent"}


@router.get("/sessions/{user_id}/output")
async def get_output(user_id: int, lines: int = 40):
    sm = SessionManager(settings)
    try:
        output = sm.capture_output(str(user_id), lines=lines)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"output": output}


@router.post("/sessions/interrupt")
async def interrupt_session(req: InterruptReq):
    sm = SessionManager(settings)
    try:
        sm.interrupt(str(req.user_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "interrupted"}


@router.post("/sessions/key")
async def send_key(req: SendKeyReq):
    sm = SessionManager(settings)
    session = sm._session_name(str(req.user_id))
    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", session, req.key],
            capture_output=True, timeout=5, check=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "key_sent"}


@router.get("/debug/install-log")
async def get_install_log():
    paths = [
        "/data/logs/opencode-install.log",
        "/tmp/logs/opencode-install.log",
        "/tmp/opencode-install.log",
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "r", errors="replace") as f:
                    return {"log": f.read()}
            except Exception as e:
                return {"error": str(e)}
    return {"error": "Installation log not found."}


@router.websocket("/ws/session/{user_id}")
async def websocket_session(websocket: WebSocket, user_id: str):
    await websocket.accept()
    sm = SessionManager(settings)
    sm.ensure_session(user_id)

    last_output = ""

    async def stream_to_client():
        nonlocal last_output
        try:
            while True:
                raw = sm.capture_output(user_id, lines=40)
                display, _ = clean_terminal_output(raw, keep_whitespace=True)
                if display and display != last_output:
                    last_output = display
                    await websocket.send_json({"type": "output", "text": display})
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WebSocket stream error: {e}")

    streamer = asyncio.create_task(stream_to_client())
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "command":
                sm.send_input(user_id, data.get("text", ""))
            elif msg_type == "key":
                session = sm._session_name(user_id)
                subprocess.run(
                    ["tmux", "send-keys", "-t", session, data.get("key", "")],
                    capture_output=True, timeout=5,
                )
            elif msg_type == "interrupt":
                sm.interrupt(user_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        streamer.cancel()
        try:
            await websocket.close()
        except Exception:
            pass


@router.get("/debug/tmux")
async def debug_tmux():
    import subprocess
    results = {}
    
    # 1. Check tmux version
    try:
        res = subprocess.run(["tmux", "-V"], capture_output=True, text=True, timeout=5)
        results["version"] = {"stdout": res.stdout.strip(), "stderr": res.stderr.strip(), "code": res.returncode}
    except Exception as e:
        results["version"] = {"error": str(e)}

    # 2. Check running sessions
    try:
        res = subprocess.run(["tmux", "list-sessions"], capture_output=True, text=True, timeout=5)
        results["sessions"] = {"stdout": res.stdout.strip(), "stderr": res.stderr.strip(), "code": res.returncode}
    except Exception as e:
        results["sessions"] = {"error": str(e)}

    # 3. Try to create a test session
    try:
        res = subprocess.run(["tmux", "new-session", "-d", "-s", "debug_test", "-c", "/tmp", "bash"], capture_output=True, text=True, timeout=5)
        results["create_session"] = {"stdout": res.stdout.strip(), "stderr": res.stderr.strip(), "code": res.returncode}
    except Exception as e:
        results["create_session"] = {"error": str(e)}

    # 4. Check if test session exists
    try:
        res = subprocess.run(["tmux", "has-session", "-t", "debug_test"], capture_output=True, text=True, timeout=5)
        results["has_session"] = {"stdout": res.stdout.strip(), "stderr": res.stderr.strip(), "code": res.returncode}
    except Exception as e:
        results["has_session"] = {"error": str(e)}

    # 5. Capture test session
    try:
        res = subprocess.run(["tmux", "capture-pane", "-p", "-t", "debug_test:0.0"], capture_output=True, text=True, timeout=5)
        results["capture"] = {"stdout": res.stdout.strip(), "stderr": res.stderr.strip(), "code": res.returncode}
    except Exception as e:
        results["capture"] = {"error": str(e)}

    # 6. Clean up test session
    try:
        subprocess.run(["tmux", "kill-session", "-t", "debug_test"], capture_output=True, timeout=5)
    except Exception:
        pass

    return results


@router.get("/debug/test-run")
async def debug_test_run():
    import subprocess
    import os
    results = {}
    
    # 1. Check if file exists
    path = "/usr/bin/opencode"
    results["exists"] = os.path.exists(path)
    if results["exists"]:
        results["size"] = os.path.getsize(path)
        results["executable"] = os.access(path, os.X_OK)
    
    # 2. Try running ls -la
    try:
        res = subprocess.run(["ls", "-la", path], capture_output=True, text=True, timeout=5)
        results["ls"] = {"stdout": res.stdout.strip(), "stderr": res.stderr.strip(), "code": res.returncode}
    except Exception as e:
        results["ls"] = {"error": str(e)}

    # 3. Try running opencode --version
    try:
        res = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
        results["run"] = {"stdout": res.stdout.strip(), "stderr": res.stderr.strip(), "code": res.returncode}
    except Exception as e:
        results["run"] = {"error": str(e)}

    return results
