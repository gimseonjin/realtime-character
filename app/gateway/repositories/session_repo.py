from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.gateway.models.session import Session
from app.gateway.models.character import Character


async def upsert_session(db: AsyncSession, session_id: str) -> None:
    now = datetime.now(timezone.utc)
    stmt = insert(Session).values(
        session_id=session_id,
        created_at=now,
        last_seen_at=now,
    ).on_conflict_do_update(
        index_elements=[Session.session_id],
        set_={"last_seen_at": now},
    )
    await db.execute(stmt)
    await db.commit()


async def create_session_with_character(
    db: AsyncSession, session_id: str, character_id: int
) -> str:
    """Create a new session bound to a character."""
    now = datetime.now(timezone.utc)
    session = Session(
        session_id=session_id,
        character_id=character_id,
        created_at=now,
        last_seen_at=now,
    )
    db.add(session)
    await db.commit()
    return session_id


async def get_session_with_character(
    db: AsyncSession, session_id: str
) -> tuple[Session, Character | None] | None:
    """Get session with its bound character."""
    stmt = select(Session).where(Session.session_id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if session is None:
        return None

    character = None
    if session.character_id:
        char_stmt = select(Character).where(Character.id == session.character_id)
        char_result = await db.execute(char_stmt)
        character = char_result.scalar_one_or_none()

    return session, character


async def update_session_last_seen(db: AsyncSession, session_id: str) -> None:
    """Update last_seen_at timestamp."""
    stmt = select(Session).where(Session.session_id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if session:
        session.last_seen_at = datetime.now(timezone.utc)
        await db.commit()
