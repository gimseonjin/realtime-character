import time
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway.services.orchestrator import Orchestrator
from app.gateway.repositories.session_repo import upsert_session
from app.gateway.repositories.turn_repo import create_turn, set_ttft, set_ttaf, finalize_turn


class TurnService:
    def __init__(self, orchestrator: Orchestrator):
        self.orchestrator = orchestrator

    async def process_message(
        self,
        db: AsyncSession,
        session_id: str,
        user_text: str,
    ) -> AsyncGenerator[dict, None]:
        """
        1. 세션 upsert
        2. 턴 생성
        3. LLM+TTS 스트리밍 (Orchestrator 위임)
        4. TTFT/TTAF 기록
        5. 턴 완료
        """
        await upsert_session(db, session_id)
        turn_id = await create_turn(db, session_id, user_text)

        t0 = time.perf_counter()
        ttft_written = False
        ttaf_written = False
        assistant_text = None

        try:
            async for event in self.orchestrator.stream_events(session_id, user_text):
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

                yield event

        except Exception as e:
            await finalize_turn(db, turn_id, assistant_text)
            yield {"type": "error", "message": str(e)}
