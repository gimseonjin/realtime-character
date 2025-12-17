from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.gateway.db import get_cache, get_db

router = APIRouter()


@router.get("/health")
async def health():
    return {"ok": True}


@router.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    await db.execute(text("select 1"))
    return {"db": "ok"}


@router.get("/health/cache")
async def health_cache(cache: Redis = Depends(get_cache)):
    try:
        await cache.ping()
        return {"cache": "ok"}
    except Exception as e:
        return {"cache": "error", "reason": str(e)}