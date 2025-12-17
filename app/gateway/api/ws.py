import json
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from app.gateway.dependencies import get_orchestrator
from app.gateway.services.orchestrator import Orchestrator

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
            text = msg["text"]

            t0 = time.perf_counter()
            first = True
            
            async for ev in orchestrator.stream_events(session_id, text):

                if first:
                    ttft_ms = (time.perf_counter() - t0) * 1000
                    print(f"[TTFT] sessionId={session_id} ttft_ms={ttft_ms:.1f}")
                    first = False

                await ws.send_json(ev)

    except WebSocketDisconnect:
        return
    except Exception as e:
        await ws.send_json({"type": "error", "message": str(e)})
