# naina/api/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from naina.agent.loop import run as agent_run

ws_router = APIRouter()

@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected")
    try:
        while True:
            data = await websocket.receive_json()
            text = data.get("text", "")
            if not text:
                continue
            logger.info(f"WS received: {text}")
            await websocket.send_json({"type": "thinking"})
            response = await agent_run(text)
            await websocket.send_json({"type": "response", "text": response})
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
