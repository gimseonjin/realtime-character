from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway.db import get_db
from app.gateway.repositories.session_repo import upsert_session

router = APIRouter()

@router.post("/sessions/{session_id}/touch")
async def touch(session_id: str, db: AsyncSession = Depends(get_db)):
    await upsert_session(db, session_id)
    return {"ok": True, "sessionId": session_id}
