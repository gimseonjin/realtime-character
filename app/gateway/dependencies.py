from contextlib import asynccontextmanager

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway.config import settings
from app.gateway.db import SessionLocal, cache
from app.gateway.services.orchestrator import Orchestrator
from app.gateway.services.turn import TurnService
from app.gateway.clients.llm import BaseLLM, MockLLM, OpenAILLM
from app.gateway.clients.tts import TTSClient
from app.gateway.clients.cache import CacheClient
from app.gateway.models.character import Character


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


def get_cache_client_instance() -> CacheClient:
    """Get cache client without Depends (for manual use)."""
    return CacheClient(cache=cache, max_turns=10)


# Clients
def get_cache_client(redis: Redis = Depends(get_cache)) -> CacheClient:
    return CacheClient(cache=redis, max_turns=10)


def get_llm() -> BaseLLM:
    """Get LLM with default settings (from env)."""
    if settings.LLM_PROVIDER == "openai":
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return OpenAILLM(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_LLM_MODEL,
            system_prompt=settings.OPENAI_LLM_SYSTEM_PROMPT,
            temperature=settings.OPENAI_LLM_TEMPERATURE,
            max_tokens=settings.OPENAI_LLM_MAX_TOKENS,
        )
    return MockLLM()


def create_llm_for_character(character: Character) -> BaseLLM:
    """Create LLM instance with character-specific settings."""
    if settings.LLM_PROVIDER == "openai":
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return OpenAILLM(
            api_key=settings.OPENAI_API_KEY,
            model=character.model,
            system_prompt=character.system_prompt,
            temperature=settings.OPENAI_LLM_TEMPERATURE,
            max_tokens=settings.OPENAI_LLM_MAX_TOKENS,
        )
    return MockLLM()


def create_tts_for_character(character: Character) -> TTSClient:
    """Create TTS client with character-specific voice."""
    return TTSClient(base_url=settings.TTS_URL, voice=character.voice)


def create_orchestrator_for_character(
    character: Character,
    cache_client: CacheClient,
) -> Orchestrator:
    """Create orchestrator with character-specific LLM and TTS."""
    llm = create_llm_for_character(character)
    tts = create_tts_for_character(character)
    return Orchestrator(cache_client=cache_client, llm=llm, tts=tts)


# Services
def get_turn_service(
    cache_client: CacheClient = Depends(get_cache_client),
) -> TurnService:
    return TurnService(
        orchestrator_factory=create_orchestrator_for_character,
        cache_client=cache_client,
    )

