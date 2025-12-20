import time
from typing import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway.repositories.session_repo import get_session_with_character, update_session_last_seen
from app.gateway.repositories.turn_repo import create_turn, set_ttft, set_ttaf, finalize_turn
from app.gateway.clients.cache import CacheClient
from app.gateway.models.character import Character
from app.gateway.services.orchestrator import Orchestrator
from app.shared.logging import get_logger

logger = get_logger(__name__)

OrchestratorFactory = Callable[[Character, CacheClient], Orchestrator]


class TurnService:
    def __init__(self, orchestrator_factory: OrchestratorFactory, cache_client: CacheClient):
        self._orchestrator_factory = orchestrator_factory
        self._cache_client = cache_client

    async def process_message(
        self,
        db: AsyncSession,
        session_id: str,
        user_text: str,
    ) -> AsyncGenerator[dict, None]:
        """
        1. 세션에서 캐릭터 조회
        2. 캐릭터 설정으로 Orchestrator 생성 (또는 기본 사용)
        3. 턴 생성
        4. LLM+TTS 스트리밍
        5. TTFT/TTAF 기록
        6. 턴 완료
        """
        # Get session and character
        result = await get_session_with_character(db, session_id)

        if result is None:
            logger.warning("session_not_found", session_id=session_id)
            raise ValueError(f"Session not found: {session_id}")

        _session, character = result
        if character is None:
            logger.warning("character_not_bound", session_id=session_id)
            raise ValueError(f"Session {session_id} has no character bound")

        await update_session_last_seen(db, session_id)
        orchestrator = self._orchestrator_factory(character, self._cache_client)

        turn_id = await create_turn(db, session_id, user_text)
        logger.info("turn_started", session_id=session_id, turn_id=turn_id, character_id=character.id)

        t0 = time.perf_counter()
        ttft_ms = None
        ttaf_ms = None
        ttft_written = False
        ttaf_written = False
        assistant_text = None

        try:
            async for event in orchestrator.stream_events(session_id, user_text):
                event_type = event.get("type")

                if event_type == "token" and not ttft_written:
                    ttft_ms = int((time.perf_counter() - t0) * 1000)
                    await set_ttft(db, turn_id, ttft_ms)
                    ttft_written = True

                if event_type == "audio_chunk" and not ttaf_written:
                    ttaf_ms = int((time.perf_counter() - t0) * 1000)
                    await set_ttaf(db, turn_id, ttaf_ms)
                    ttaf_written = True

                if event_type == "done":
                    assistant_text = event.get("assistant_text")
                    await finalize_turn(db, turn_id, assistant_text)
                    duration_ms = int((time.perf_counter() - t0) * 1000)
                    logger.info(
                        "turn_completed",
                        session_id=session_id,
                        turn_id=turn_id,
                        ttft_ms=ttft_ms,
                        ttaf_ms=ttaf_ms,
                        duration_ms=duration_ms,
                    )

                yield event

        except Exception as e:
            await finalize_turn(db, turn_id, assistant_text)
            logger.error("turn_error", session_id=session_id, turn_id=turn_id, error=str(e))
            yield {"type": "error", "message": str(e)}
