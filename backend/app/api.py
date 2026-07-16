from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from backend.app.config import settings
from sessions.db import SessionStore
from core.session_manager import SessionManager

router = APIRouter()

class CreateSessionReq(BaseModel):
    user_id: int
    project: str | None = "default"

class SendInputReq(BaseModel):
    user_id: int
    text: str

class InterruptReq(BaseModel):
    user_id: int


@router.post("/sessions/new")
async def new_session(req: CreateSessionReq):
    sm = SessionManager(settings)
    try:
        sm.ensure_session(str(req.user_id), project=req.project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "created"}


@router.get("/sessions/{user_id}/status")
async def session_status(user_id: int):
    store = SessionStore()
    info = store.get_session(user_id)
    if not info:
        raise HTTPException(status_code=404, detail="no session")
    return info


@router.post("/sessions/send")
async def send_input(req: SendInputReq):
    sm = SessionManager(settings)
    try:
        sm.send_input(str(req.user_id), req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "sent"}


@router.get("/sessions/{user_id}/output")
async def get_output(user_id: int, lines: int = 200):
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


import httpx

@router.get("/debug/ping-telegram")
async def ping_telegram():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://api.telegram.org")
            return {"status": resp.status_code, "text": resp.text[:100]}
    except Exception as e:
        return {"error": type(e).__name__, "message": str(e)}


@router.get("/debug/ping-url")
async def ping_url(url: str = "https://www.google.com"):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            return {"status": resp.status_code, "text": resp.text[:100]}
    except Exception as e:
        return {"error": type(e).__name__, "message": str(e)}


