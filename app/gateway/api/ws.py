import json
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from app.gateway.dependencies import get_orchestrator, get_db_context
from app.gateway.services.orchestrator import Orchestrator
from app.gateway.repositories.session_repo import upsert_session
from app.gateway.repositories.turn_repo import finalize_turn, set_ttaf, set_ttft, create_turn

router = APIRouter()


@router.websocket("/ws")
async def ws_chat(
    ws: WebSocket,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            session_id = msg["sessionId"]
            user_text = msg["text"]

            t0 = time.perf_counter()
            ttft_written = False
            ttaf_written = False
            turn_id = None
            assistant_text = None

            # 메시지 단위로 DB 세션 획득/반환
            async with get_db_context() as db:
                await upsert_session(db, session_id)
                turn_id = await create_turn(db, session_id, user_text)

                try:
                    async for event in orchestrator.stream_events(session_id, user_text):
                        event_type = event.get("type")

                        if event_type == "token":
                            if not ttft_written:
                                ttft_ms = int((time.perf_counter() - t0) * 1000)
                                await set_ttft(db, turn_id, ttft_ms)
                                ttft_written = True

                            await ws.send_json(event)
                            continue

                        if event_type == "audio_chunk":
                            if not ttaf_written:
                                ttaf_ms = int((time.perf_counter() - t0) * 1000)
                                await set_ttaf(db, turn_id, ttaf_ms)
                                ttaf_written = True

                            await ws.send_json(event)
                            continue

                        if event_type == "done":
                            assistant_text = event.get("assistant_text")
                            await finalize_turn(db, turn_id, assistant_text)
                            await ws.send_json(event)
                            break

                        await ws.send_json(event)

                except Exception as e:
                    if turn_id:
                        await finalize_turn(db, turn_id, assistant_text)
                    await ws.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        return
    except Exception as e:
        await ws.send_json({"type": "error", "message": str(e)})
