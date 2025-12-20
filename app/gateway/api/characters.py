from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway.dependencies import get_db
from app.gateway.repositories.character_repo import (
    create_character,
    get_character,
    list_characters,
    update_character,
    delete_character,
)


router = APIRouter(prefix="/characters", tags=["characters"])


class CharacterCreate(BaseModel):
    name: str
    system_prompt: str = "You are a helpful assistant."
    model: str = "gpt-4o-mini"
    voice: str = "alloy"


class CharacterUpdate(BaseModel):
    name: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    voice: str | None = None


@router.post("")
async def create_character_endpoint(
    body: CharacterCreate,
    db: AsyncSession = Depends(get_db),
):
    character_id = await create_character(
        db,
        name=body.name,
        system_prompt=body.system_prompt,
        model=body.model,
        voice=body.voice,
    )
    return {"id": character_id}


@router.get("")
async def list_characters_endpoint(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    characters = await list_characters(db, limit)
    return [
        {
            "id": c.id,
            "name": c.name,
            "system_prompt": c.system_prompt,
            "model": c.model,
            "voice": c.voice,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in characters
    ]


@router.get("/{character_id}")
async def get_character_endpoint(
    character_id: int,
    db: AsyncSession = Depends(get_db),
):
    character = await get_character(db, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return {
        "id": character.id,
        "name": character.name,
        "system_prompt": character.system_prompt,
        "model": character.model,
        "voice": character.voice,
        "created_at": character.created_at,
        "updated_at": character.updated_at,
    }


@router.patch("/{character_id}")
async def update_character_endpoint(
    character_id: int,
    body: CharacterUpdate,
    db: AsyncSession = Depends(get_db),
):
    updated = await update_character(
        db,
        character_id,
        name=body.name,
        system_prompt=body.system_prompt,
        model=body.model,
        voice=body.voice,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"ok": True}


@router.delete("/{character_id}")
async def delete_character_endpoint(
    character_id: int,
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_character(db, character_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"ok": True}
