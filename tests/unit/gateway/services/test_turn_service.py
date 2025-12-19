from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.gateway.services.turn import TurnService


class TestTurnService:
    """TurnService.process_message() 테스트"""

    @pytest.fixture
    def mock_orchestrator(self):
        orchestrator = MagicMock()

        async def fake_stream_events(session_id, user_text):
            yield {"type": "token", "text": "H"}
            yield {"type": "token", "text": "i"}
            yield {"type": "audio_chunk", "seq": 1, "format": "wav", "data": "abc"}
            yield {"type": "done", "assistant_text": "Hi"}

        orchestrator.stream_events = fake_stream_events
        return orchestrator

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def turn_service(self, mock_orchestrator):
        return TurnService(orchestrator=mock_orchestrator)

    @patch("app.gateway.services.turn.upsert_session")
    @patch("app.gateway.services.turn.create_turn")
    @patch("app.gateway.services.turn.set_ttft")
    @patch("app.gateway.services.turn.set_ttaf")
    @patch("app.gateway.services.turn.finalize_turn")
    async def test_process_message_yields_all_events(
        self,
        mock_finalize,
        mock_set_ttaf,
        mock_set_ttft,
        mock_create_turn,
        mock_upsert,
        turn_service,
        mock_db,
    ):
        """모든 이벤트가 순서대로 yield 되는지 확인"""
        mock_create_turn.return_value = 1

        events = []
        async for event in turn_service.process_message(mock_db, "session-1", "Hello"):
            events.append(event)

        assert len(events) == 4
        assert events[0] == {"type": "token", "text": "H"}
        assert events[1] == {"type": "token", "text": "i"}
        assert events[2]["type"] == "audio_chunk"
        assert events[3]["type"] == "done"

    @patch("app.gateway.services.turn.upsert_session")
    @patch("app.gateway.services.turn.create_turn")
    @patch("app.gateway.services.turn.set_ttft")
    @patch("app.gateway.services.turn.set_ttaf")
    @patch("app.gateway.services.turn.finalize_turn")
    async def test_session_upserted_before_turn_creation(
        self,
        mock_finalize,
        mock_set_ttaf,
        mock_set_ttft,
        mock_create_turn,
        mock_upsert,
        turn_service,
        mock_db,
    ):
        """세션 upsert가 턴 생성 전에 호출되는지 확인"""
        mock_create_turn.return_value = 1
        call_order = []

        async def track_upsert(*args):
            call_order.append("upsert")

        async def track_create(*args):
            call_order.append("create")
            return 1

        mock_upsert.side_effect = track_upsert
        mock_create_turn.side_effect = track_create

        async for _ in turn_service.process_message(mock_db, "session-1", "Hello"):
            pass

        assert call_order == ["upsert", "create"]

    @patch("app.gateway.services.turn.upsert_session")
    @patch("app.gateway.services.turn.create_turn")
    @patch("app.gateway.services.turn.set_ttft")
    @patch("app.gateway.services.turn.set_ttaf")
    @patch("app.gateway.services.turn.finalize_turn")
    async def test_ttft_recorded_on_first_token(
        self,
        mock_finalize,
        mock_set_ttaf,
        mock_set_ttft,
        mock_create_turn,
        mock_upsert,
        turn_service,
        mock_db,
    ):
        """첫 번째 토큰에서 TTFT가 기록되는지 확인"""
        mock_create_turn.return_value = 42

        async for _ in turn_service.process_message(mock_db, "session-1", "Hello"):
            pass

        # TTFT는 한 번만 호출되어야 함
        mock_set_ttft.assert_called_once()
        call_args = mock_set_ttft.call_args
        assert call_args[0][0] == mock_db  # db
        assert call_args[0][1] == 42  # turn_id
        assert isinstance(call_args[0][2], int)  # ttft_ms

    @patch("app.gateway.services.turn.upsert_session")
    @patch("app.gateway.services.turn.create_turn")
    @patch("app.gateway.services.turn.set_ttft")
    @patch("app.gateway.services.turn.set_ttaf")
    @patch("app.gateway.services.turn.finalize_turn")
    async def test_ttaf_recorded_on_first_audio_chunk(
        self,
        mock_finalize,
        mock_set_ttaf,
        mock_set_ttft,
        mock_create_turn,
        mock_upsert,
        turn_service,
        mock_db,
    ):
        """첫 번째 audio_chunk에서 TTAF가 기록되는지 확인"""
        mock_create_turn.return_value = 42

        async for _ in turn_service.process_message(mock_db, "session-1", "Hello"):
            pass

        # TTAF는 한 번만 호출되어야 함
        mock_set_ttaf.assert_called_once()
        call_args = mock_set_ttaf.call_args
        assert call_args[0][0] == mock_db
        assert call_args[0][1] == 42
        assert isinstance(call_args[0][2], int)

    @patch("app.gateway.services.turn.upsert_session")
    @patch("app.gateway.services.turn.create_turn")
    @patch("app.gateway.services.turn.set_ttft")
    @patch("app.gateway.services.turn.set_ttaf")
    @patch("app.gateway.services.turn.finalize_turn")
    async def test_turn_finalized_on_done(
        self,
        mock_finalize,
        mock_set_ttaf,
        mock_set_ttft,
        mock_create_turn,
        mock_upsert,
        turn_service,
        mock_db,
    ):
        """done 이벤트에서 턴이 finalize 되는지 확인"""
        mock_create_turn.return_value = 42

        async for _ in turn_service.process_message(mock_db, "session-1", "Hello"):
            pass

        mock_finalize.assert_called_once_with(mock_db, 42, "Hi")

    @patch("app.gateway.services.turn.upsert_session")
    @patch("app.gateway.services.turn.create_turn")
    @patch("app.gateway.services.turn.set_ttft")
    @patch("app.gateway.services.turn.set_ttaf")
    @patch("app.gateway.services.turn.finalize_turn")
    async def test_error_handling_yields_error_event(
        self,
        mock_finalize,
        mock_set_ttaf,
        mock_set_ttft,
        mock_create_turn,
        mock_upsert,
        mock_db,
    ):
        """예외 발생 시 error 이벤트가 yield 되는지 확인"""
        mock_create_turn.return_value = 1

        orchestrator = MagicMock()

        async def failing_stream(session_id, user_text):
            yield {"type": "token", "text": "H"}
            raise ValueError("LLM error")

        orchestrator.stream_events = failing_stream
        turn_service = TurnService(orchestrator=orchestrator)

        events = []
        async for event in turn_service.process_message(mock_db, "session-1", "Hello"):
            events.append(event)

        assert events[-1]["type"] == "error"
        assert "LLM error" in events[-1]["message"]

    @patch("app.gateway.services.turn.upsert_session")
    @patch("app.gateway.services.turn.create_turn")
    @patch("app.gateway.services.turn.set_ttft")
    @patch("app.gateway.services.turn.set_ttaf")
    @patch("app.gateway.services.turn.finalize_turn")
    async def test_turn_finalized_even_on_error(
        self,
        mock_finalize,
        mock_set_ttaf,
        mock_set_ttft,
        mock_create_turn,
        mock_upsert,
        mock_db,
    ):
        """예외 발생 시에도 턴이 finalize 되는지 확인"""
        mock_create_turn.return_value = 42

        orchestrator = MagicMock()

        async def failing_stream(session_id, user_text):
            yield {"type": "token", "text": "H"}
            raise ValueError("LLM error")

        orchestrator.stream_events = failing_stream
        turn_service = TurnService(orchestrator=orchestrator)

        async for _ in turn_service.process_message(mock_db, "session-1", "Hello"):
            pass

        mock_finalize.assert_called_once()


class TestTurnServiceNoAudio:
    """오디오 청크가 없는 경우 테스트"""

    @patch("app.gateway.services.turn.upsert_session")
    @patch("app.gateway.services.turn.create_turn")
    @patch("app.gateway.services.turn.set_ttft")
    @patch("app.gateway.services.turn.set_ttaf")
    @patch("app.gateway.services.turn.finalize_turn")
    async def test_ttaf_not_called_without_audio(
        self,
        mock_finalize,
        mock_set_ttaf,
        mock_set_ttft,
        mock_create_turn,
        mock_upsert,
    ):
        """오디오 청크가 없으면 TTAF가 호출되지 않는지 확인"""
        mock_create_turn.return_value = 1
        mock_db = AsyncMock()

        orchestrator = MagicMock()

        async def stream_without_audio(session_id, user_text):
            yield {"type": "token", "text": "Hi"}
            yield {"type": "done", "assistant_text": "Hi"}

        orchestrator.stream_events = stream_without_audio
        turn_service = TurnService(orchestrator=orchestrator)

        async for _ in turn_service.process_message(mock_db, "session-1", "Hello"):
            pass

        mock_set_ttaf.assert_not_called()
