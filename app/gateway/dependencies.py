from contextlib import asynccontextmanager

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway.config import settings
from app.gateway.db import SessionLocal, cache
from app.gateway.services.orchestrator import Orchestrator
from app.gateway.services.session_store import SessionStore
from app.gateway.services.llm_client import MockLLM
from app.gateway.services.tts_client import TTSClient
from app.gateway.services.turn_service import TurnService


# DB session (for FastAPI Depends)
async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


# DB session (for manual context manager - WebSocket 등)
@asynccontextmanager
async def get_db_context() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


# Cache
async def get_cache() -> Redis:
    return cache


# Services
def get_session_store(redis: Redis = Depends(get_cache)) -> SessionStore:
    return SessionStore(cache=redis, max_turns=10)


def get_orchestrator(
    store: SessionStore = Depends(get_session_store),
) -> Orchestrator:
    llm = MockLLM()
    tts = TTSClient(base_url=settings.TTS_URL)
    return Orchestrator(store=store, llm=llm, tts=tts)


def get_turn_service(
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> TurnService:
    return TurnService(orchestrator=orchestrator)

