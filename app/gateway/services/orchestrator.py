import asyncio
import base64

from app.gateway.services.tts_client import TTSClient
from app.gateway.services.llm_client import MockLLM
from app.gateway.services.session_store import SessionStore

PUNCT = {".", "?", "!", "\n"}

class Orchestrator:
    def __init__(self, tts_url: str):
        self.store = SessionStore()
        self.llm = MockLLM()
        self.tts = TTSClient(tts_url)

    async def stream_events(self, session_id: str, user_text: str):
        self.store.append_user(session_id, user_text)

        event_q: asyncio.Queue[dict] = asyncio.Queue()
        tts_text_q: asyncio.Queue[tuple[int, str]] = asyncio.Queue()

        async def token_producer():
            buf = ""
            seq = 0
            async for tok in self.llm.stream(user_text, self.store.get_history(session_id)):
                await event_q.put({"type": "token", "text": tok})

                buf += tok
                if len(buf) >= 60 or any(p in buf for p in PUNCT):
                    seq += 1
                    await tts_text_q.put((seq, buf.strip()))
                    buf = ""

            if buf.strip():
                seq += 1
                await tts_text_q.put((seq, buf.strip()))

            await tts_text_q.put((-1, ""))  # 종료 신호

        async def tts_producer():
            while True:
                seq, chunk = await tts_text_q.get()
                if seq == -1:
                    break
                audio_bytes = await self.tts.synthesize(chunk, fmt="wav")
                b64 = base64.b64encode(audio_bytes).decode("ascii")
                await event_q.put({
                    "type": "audio_chunk",
                    "seq": seq,
                    "format": "wav",
                    "data": b64,
                })

            await event_q.put({"type": "done"})

        # 두 생산자를 동시에 돌림
        tok_task = asyncio.create_task(token_producer())
        tts_task = asyncio.create_task(tts_producer())

        try:
            while True:
                ev = await event_q.get()
                yield ev
                if ev["type"] == "done":
                    break
        finally:
            tok_task.cancel()
            tts_task.cancel()
