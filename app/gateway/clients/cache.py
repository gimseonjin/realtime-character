from collections import defaultdict, deque

from redis.asyncio import Redis

from app.gateway.schemas.message import Message


class CacheClient:
    """Redis 기반 세션 히스토리 캐시 (LLM 컨텍스트용)"""

    def __init__(
        self,
        cache: Redis,
        max_turns: int = 10,
        ttl_seconds: int = 60 * 60 * 24,
    ):
        self._cache = cache
        self._max_turns = max_turns
        self._ttl = ttl_seconds
        self._hist: dict[str, deque[Message]] = defaultdict(lambda: deque(maxlen=max_turns * 2))

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}:history"

    def append_user(self, session_id: str, content: str):
        self._hist[session_id].append(Message(role="user", content=content))

    def append_assistant(self, session_id: str, content: str):
        self._hist[session_id].append(Message(role="assistant", content=content))

    def get_history_local(self, session_id: str) -> list[Message]:
        return list(self._hist[session_id])

    async def flush_last_turn_to_cache(self, session_id: str, user_text: str, assistant_text: str):
        key = self._key(session_id)

        user_msg = Message(role="user", content=user_text).model_dump_json()
        asst_msg = Message(role="assistant", content=assistant_text).model_dump_json()

        try:
            await self._cache.lpush(key, asst_msg)
            await self._cache.lpush(key, user_msg)

            await self._cache.ltrim(key, 0, self._max_turns * 2 - 1)
            await self._cache.expire(key, self._ttl)
        except Exception:
            return

    async def get_history(self, session_id: str) -> list[Message]:
        key = self._key(session_id)

        try:
            raw = await self._cache.lrange(key, 0, -1)
            if raw:
                msgs = [Message.model_validate_json(x) for x in reversed(raw)]

                self._hist[session_id].clear()
                self._hist[session_id].extend(msgs)
                return msgs
        except Exception:
            pass

        return self.get_history_local(session_id)
