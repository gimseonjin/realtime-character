import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway.dependencies import get_db
from app.gateway.repositories.session_repo import (
    upsert_session,
    create_session_with_character,
)
from app.gateway.repositories.character_repo import get_character


router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    character_id: int


def generate_session_id() -> str:
    return f"session-{secrets.token_urlsafe(16)}"


@router.post("")
async def create_session(
    body: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new session bound to a character."""
    # Verify character exists
    character = await get_character(db, body.character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")

    session_id = generate_session_id()
    await create_session_with_character(db, session_id, body.character_id)
    return {"sessionId": session_id}


@router.post("/{session_id}/touch")
async def touch(session_id: str, db: AsyncSession = Depends(get_db)):
    await upsert_session(db, session_id)
    return {"ok": True, "sessionId": session_id}
