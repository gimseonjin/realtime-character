from redis.asyncio import Redis
from fastapi import Depends

from app.gateway.config import settings
from app.gateway.services.orchestrator import Orchestrator
from app.gateway.db import get_cache
from app.gateway.services.session_store import SessionStore
from app.gateway.services.llm_client import MockLLM
from app.gateway.services.tts_client import TTSClient


def get_session_store(redis: Redis = Depends(get_cache)) -> SessionStore:
    return SessionStore(cache=redis, max_turns=10)

def get_orchestrator(
    store: SessionStore = Depends(get_session_store),
) -> Orchestrator:
    llm = MockLLM()
    tts = TTSClient(base_url=settings.TTS_URL)
    return Orchestrator(store=store, llm=llm, tts=tts)

