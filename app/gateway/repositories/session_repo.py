from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.gateway.models.session import Session


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
