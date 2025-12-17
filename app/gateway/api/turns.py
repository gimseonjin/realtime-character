from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.gateway.db import get_db
from app.gateway.repositories.session_repo import upsert_session
from app.gateway.repositories.turn_repo import create_turn, set_ttft, set_ttaf, finalize_turn, get_recent_turns

router = APIRouter()

@router.post("/sessions/{session_id}/turns/start")
async def start_turn(session_id: str, text: str, db: AsyncSession = Depends(get_db) ):
    await upsert_session(db, session_id)
    turn_id = await create_turn(db, session_id, text)
    return {"turnId": turn_id}

@router.post("/turns/{turn_id}/ttft")
async def update_ttft(turn_id: int, ms: int, db: AsyncSession = Depends(get_db)):
    await set_ttft(db, turn_id, ms)
    return {"ok": True}

@router.post("/turns/{turn_id}/ttaf")
async def update_ttaf(turn_id: int, ms: int, db: AsyncSession = Depends(get_db)):
    await set_ttaf(db, turn_id, ms)
    return {"ok": True}

@router.post("/turns/{turn_id}/finalize")
async def end_turn(turn_id: int, assistant: str = "", db: AsyncSession = Depends(get_db)):
    await finalize_turn(db, turn_id, assistant_text=assistant or None)
    return {"ok": True}

@router.get("/sessions/{session_id}/turns")
async def list_turns(session_id: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    turns = await get_recent_turns(db, session_id, limit)
    return [
        {
            "id": t.id,
            "user_text": t.user_text,
            "assistant_text": t.assistant_text,
            "ttft_ms": t.ttft_ms,
            "ttaf_ms": t.ttaf_ms,
            "created_at": t.created_at,
            "completed_at": t.completed_at,
        }
        for t in turns
    ]
