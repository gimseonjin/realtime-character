import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from app.gateway.dependencies import get_turn_service, get_db_context
from app.gateway.services.turn import TurnService

router = APIRouter()


@router.websocket("/ws")
async def ws_chat(
    ws: WebSocket,
    turn_service: TurnService = Depends(get_turn_service),
):
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            # 제어 문자 제거
            clean = "".join(ch for ch in raw if ch >= " ").strip()
            msg = json.loads(clean)

            session_id = msg["sessionId"]
            user_text = msg["text"]

            async with get_db_context() as db:
                async for event in turn_service.process_message(db, session_id, user_text):
                    await ws.send_json(event)
                    if event.get("type") == "done":
                        break

    except WebSocketDisconnect:
        return
    except Exception as e:
        await ws.send_json({"type": "error", "message": str(e)})
