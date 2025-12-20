from datetime import datetime, timezone
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway.models.character import Character


async def create_character(
    db: AsyncSession,
    name: str,
    system_prompt: str = "You are a helpful assistant.",
    model: str = "gpt-4o-mini",
    voice: str = "alloy",
) -> int:
    character = Character(
        name=name,
        system_prompt=system_prompt,
        model=model,
        voice=voice,
    )
    db.add(character)
    await db.flush()
    await db.commit()
    return character.id


async def get_character(db: AsyncSession, character_id: int) -> Character | None:
    stmt = select(Character).where(Character.id == character_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def list_characters(db: AsyncSession, limit: int = 100) -> list[Character]:
    stmt = select(Character).order_by(Character.updated_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def update_character(
    db: AsyncSession,
    character_id: int,
    name: str | None = None,
    system_prompt: str | None = None,
    model: str | None = None,
    voice: str | None = None,
) -> bool:
    values: dict = {"updated_at": datetime.now(timezone.utc)}
    if name is not None:
        values["name"] = name
    if system_prompt is not None:
        values["system_prompt"] = system_prompt
    if model is not None:
        values["model"] = model
    if voice is not None:
        values["voice"] = voice

    result = await db.execute(
        update(Character).where(Character.id == character_id).values(**values)
    )
    await db.commit()
    return result.rowcount > 0


async def delete_character(db: AsyncSession, character_id: int) -> bool:
    result = await db.execute(
        delete(Character).where(Character.id == character_id)
    )
    await db.commit()
    return result.rowcount > 0
