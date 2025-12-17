from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway.models.turn import Turn

async def create_turn(db: AsyncSession, session_id: str, user_text: str) -> int:
    turn = Turn(session_id=session_id, user_text=user_text)
    db.add(turn)
    await db.flush()  # id 생성
    await db.commit()
    return turn.id

async def set_ttft(db: AsyncSession, turn_id: int, ttft_ms: int) -> None:
    await db.execute(
        update(Turn).where(Turn.id == turn_id).values(ttft_ms=ttft_ms)
    )
    await db.commit()

async def set_ttaf(db: AsyncSession, turn_id: int, ttaf_ms: int) -> None:
    await db.execute(
        update(Turn).where(Turn.id == turn_id).values(ttaf_ms=ttaf_ms)
    )
    await db.commit()

async def finalize_turn(db: AsyncSession, turn_id: int, assistant_text: str | None) -> None:
    await db.execute(
        update(Turn)
        .where(Turn.id == turn_id)
        .values(assistant_text=assistant_text, completed_at=datetime.now(timezone.utc))
    )
    await db.commit()

async def get_recent_turns(db: AsyncSession, session_id: str, limit: int = 50):
    stmt = (
        select(Turn)
        .where(Turn.session_id == session_id)
        .order_by(Turn.id.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()
