import asyncio
import base64

from app.gateway.services.tts_client import TTSClient
from app.gateway.services.llm_client import MockLLM
from app.gateway.services.session_store import SessionStore

PUNCT = {".", "?", "!", "\n"}

class Orchestrator:
    def __init__(self, store: SessionStore, tts: TTSClient, llm: MockLLM):
        self.store = store
        self.llm = llm
        self.tts = tts

    async def stream_events(self, session_id: str, user_text: str):
        history = await self.store.get_history(session_id)
        self.store.append_user(session_id, user_text)

        user_msg = {"role": "user", "text": user_text}
        llm_history = history + [user_msg]

        event_q: asyncio.Queue[dict] = asyncio.Queue()
        tts_text_q: asyncio.Queue[tuple[int, str]] = asyncio.Queue()

        assistant_buf = []

        async def token_producer():
            buf = ""
            seq = 0
            async for tok in self.llm.stream(user_text, llm_history):
                assistant_buf.append(tok)
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

            assistant_text = "".join(assistant_buf).strip() or None
            if assistant_text:
                self.store.append_assistant(session_id, assistant_text)
                await self.store.flush_last_turn_to_cache(session_id, user_text, assistant_text)

            await event_q.put({"type": "done", "assistant_text": assistant_text})

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
