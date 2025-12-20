import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

import httpx

from app.gateway.schemas.message import Message


class LLMError(Exception):
    """Base exception for LLM errors."""

    pass


class BaseLLM(ABC):
    @abstractmethod
    async def stream(
        self, user_text: str, history: list[Message]
    ) -> AsyncIterator[str]:
        """Stream tokens from the LLM."""
        pass


class MockLLM(BaseLLM):
    """Mock LLM for testing - echoes input character by character."""

    async def stream(
        self, user_text: str, history: list[Message]
    ) -> AsyncIterator[str]:
        reply = f"echo: {user_text}"
        for ch in reply:
            await asyncio.sleep(0.02)
            yield ch


class OpenAILLM(BaseLLM):
    """OpenAI Chat Completion with streaming.

    스트리밍 응답은 Server-Sent Events (SSE) 형식으로 옵니다.
    각 청크는 "data: {json}" 형태이고, 스트림 종료 시 "data: [DONE]"이 전송돼요.

    참고: https://platform.openai.com/docs/api-reference/streaming
    """

    OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def stream(
        self, user_text: str, history: list[Message]
    ) -> AsyncIterator[str]:
        messages = self._build_messages(user_text, history)

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST",
                    self.OPENAI_CHAT_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                        "stream": True,
                    },
                ) as response:
                    if response.status_code == 401:
                        raise LLMError("Invalid OpenAI API key")
                    elif response.status_code == 429:
                        raise LLMError("OpenAI rate limit exceeded")
                    elif response.status_code >= 400:
                        raise LLMError(f"OpenAI API error: {response.status_code}")

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                import json

                                chunk = json.loads(data)
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    yield content
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue

            except httpx.TimeoutException as e:
                raise LLMError("OpenAI API timeout") from e
            except httpx.RequestError as e:
                raise LLMError(f"Network error: {e}") from e

    def _build_messages(
        self, user_text: str, history: list[Message]
    ) -> list[dict[str, str]]:
        messages = []

        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": user_text})

        return messages
