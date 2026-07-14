from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from backend.app.config import settings
from sessions.db import SessionStore
from core.session_manager import SessionManager

router = APIRouter()

class CreateSessionReq(BaseModel):
    user_id: int
    project: str | None = "default"


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
