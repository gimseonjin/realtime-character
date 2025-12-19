import base64
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.gateway.services.orchestrator import Orchestrator, PUNCT


class TestOrchestrator:
    """Orchestrator.stream_events() 테스트"""

    @pytest.fixture
    def mock_cache_client(self):
        cache = MagicMock()
        cache.get_history = AsyncMock(return_value=[])
        cache.append_user = MagicMock()
        cache.append_assistant = MagicMock()
        cache.flush_last_turn_to_cache = AsyncMock()
        return cache

    @pytest.fixture
    def mock_tts_client(self):
        tts = MagicMock()
        tts.synthesize = AsyncMock(return_value=b"fake_audio_bytes")
        return tts

    @pytest.fixture
    def mock_llm(self):
        llm = MagicMock()

        async def fake_stream(user_text, history):
            for char in "Hello!":
                yield char

        llm.stream = fake_stream
        return llm

    @pytest.fixture
    def orchestrator(self, mock_cache_client, mock_tts_client, mock_llm):
        return Orchestrator(
            cache_client=mock_cache_client,
            tts=mock_tts_client,
            llm=mock_llm,
        )

    async def test_stream_events_yields_tokens(self, orchestrator):
        """토큰 이벤트가 순서대로 yield 되는지 확인"""
        events = []
        async for event in orchestrator.stream_events("session-1", "Hi"):
            events.append(event)

        token_events = [e for e in events if e["type"] == "token"]
        assert len(token_events) == 6  # "Hello!" = 6글자
        assert "".join(e["text"] for e in token_events) == "Hello!"

    async def test_stream_events_yields_done_event(self, orchestrator):
        """done 이벤트가 마지막에 yield 되는지 확인"""
        events = []
        async for event in orchestrator.stream_events("session-1", "Hi"):
            events.append(event)

        assert events[-1]["type"] == "done"
        assert events[-1]["assistant_text"] == "Hello!"

    async def test_stream_events_yields_audio_chunks(self, orchestrator):
        """audio_chunk 이벤트가 yield 되는지 확인"""
        events = []
        async for event in orchestrator.stream_events("session-1", "Hi"):
            events.append(event)

        audio_events = [e for e in events if e["type"] == "audio_chunk"]
        assert len(audio_events) >= 1

        for audio_event in audio_events:
            assert audio_event["format"] == "wav"
            assert "data" in audio_event
            # base64 디코딩 가능한지 확인
            decoded = base64.b64decode(audio_event["data"])
            assert decoded == b"fake_audio_bytes"

    async def test_cache_operations_called(self, orchestrator, mock_cache_client):
        """캐시 연산이 올바르게 호출되는지 확인"""
        events = []
        async for event in orchestrator.stream_events("session-1", "Hi"):
            events.append(event)

        mock_cache_client.get_history.assert_called_once_with("session-1")
        mock_cache_client.append_user.assert_called_once_with("session-1", "Hi")
        mock_cache_client.append_assistant.assert_called_once_with("session-1", "Hello!")
        mock_cache_client.flush_last_turn_to_cache.assert_called_once_with(
            "session-1", "Hi", "Hello!"
        )

    async def test_tts_called_with_text_chunks(self, orchestrator, mock_tts_client):
        """TTS가 텍스트 청크와 함께 호출되는지 확인"""
        events = []
        async for event in orchestrator.stream_events("session-1", "Hi"):
            events.append(event)

        # "Hello!" 에서 '!' 가 PUNCT 이므로 청킹됨
        mock_tts_client.synthesize.assert_called()

    async def test_history_passed_to_llm(self, mock_cache_client, mock_tts_client):
        """기존 히스토리가 LLM에 전달되는지 확인"""
        existing_history = [
            {"role": "user", "text": "Previous question"},
            {"role": "assistant", "text": "Previous answer"},
        ]
        mock_cache_client.get_history = AsyncMock(return_value=existing_history)

        received_history = None

        async def capture_stream(user_text, history):
            nonlocal received_history
            received_history = history
            yield "OK"

        mock_llm = MagicMock()
        mock_llm.stream = capture_stream

        orchestrator = Orchestrator(
            cache_client=mock_cache_client,
            tts=mock_tts_client,
            llm=mock_llm,
        )

        async for _ in orchestrator.stream_events("session-1", "New question"):
            pass

        # 기존 히스토리 + 새 user 메시지
        assert len(received_history) == 3
        assert received_history[0] == {"role": "user", "text": "Previous question"}
        assert received_history[1] == {"role": "assistant", "text": "Previous answer"}
        assert received_history[2] == {"role": "user", "text": "New question"}


class TestChunkingLogic:
    """토큰 청킹 로직 테스트 (60자 또는 구두점 기준)"""

    @pytest.fixture
    def mock_cache_client(self):
        cache = MagicMock()
        cache.get_history = AsyncMock(return_value=[])
        cache.append_user = MagicMock()
        cache.append_assistant = MagicMock()
        cache.flush_last_turn_to_cache = AsyncMock()
        return cache

    @pytest.fixture
    def mock_tts_client(self):
        tts = MagicMock()
        tts.synthesize = AsyncMock(return_value=b"audio")
        return tts

    async def test_chunks_on_punctuation(self, mock_cache_client, mock_tts_client):
        """구두점에서 청킹되는지 확인"""
        chunks_sent_to_tts = []

        async def capture_synthesize(text, fmt):
            chunks_sent_to_tts.append(text)
            return b"audio"

        mock_tts_client.synthesize = capture_synthesize

        async def stream_with_punct(user_text, history):
            for char in "Hi. Bye!":
                yield char

        mock_llm = MagicMock()
        mock_llm.stream = stream_with_punct

        orchestrator = Orchestrator(
            cache_client=mock_cache_client,
            tts=mock_tts_client,
            llm=mock_llm,
        )

        async for _ in orchestrator.stream_events("s1", "test"):
            pass

        # "Hi." 와 "Bye!" 두 청크로 분리되어야 함
        assert len(chunks_sent_to_tts) == 2
        assert chunks_sent_to_tts[0] == "Hi."
        assert chunks_sent_to_tts[1] == "Bye!"

    async def test_chunks_on_60_chars(self, mock_cache_client, mock_tts_client):
        """60자 이상에서 청킹되는지 확인"""
        chunks_sent_to_tts = []

        async def capture_synthesize(text, fmt):
            chunks_sent_to_tts.append(text)
            return b"audio"

        mock_tts_client.synthesize = capture_synthesize

        # 구두점 없이 70자 생성
        long_text = "a" * 70

        async def stream_long(user_text, history):
            for char in long_text:
                yield char

        mock_llm = MagicMock()
        mock_llm.stream = stream_long

        orchestrator = Orchestrator(
            cache_client=mock_cache_client,
            tts=mock_tts_client,
            llm=mock_llm,
        )

        async for _ in orchestrator.stream_events("s1", "test"):
            pass

        # 60자 + 10자 두 청크로 분리
        assert len(chunks_sent_to_tts) == 2
        assert len(chunks_sent_to_tts[0]) == 60
        assert len(chunks_sent_to_tts[1]) == 10


class TestPunctConstant:
    """PUNCT 상수 테스트"""

    def test_punct_contains_expected_chars(self):
        assert "." in PUNCT
        assert "?" in PUNCT
        assert "!" in PUNCT
        assert "\n" in PUNCT
