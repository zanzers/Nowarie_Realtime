import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from pydantic import ValidationError

from app.lib.lib_Main import savedMessage
from app.connection_manager import ConnectionManager
from app.db.schemas.schemas import MessageEvent, IncomingMessage
from app.db.message_repository import get_messages


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nowarie Realtime",
    description="A reusable real-time backend for messaging and future multiplayer applications.",
    version="0.1.0",
)

manager = ConnectionManager()


@app.get("/health")
async def health_check():
    return {
        "status":"Healthy",
        "service": "nowarie-realtime",
        "version":"0.1.0"
    }

@app.get("/rooms/{room_id}/messages")
async def get_room_messages(room_id: str, limit: int = Query(default=50, ge=1, le=100)):
    messages = get_messages(room_id, limit)
    return {
        "room_id": room_id,
        "messages": messages,
    }





@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
   
    await manager.connect(websocket, room_id)
    logging.info("Client connected to room %s", room_id)

    try:
        while True:
            try:
                payload = await websocket.receive_json()
                incoming = IncomingMessage.model_validate(payload)
                message = MessageEvent(**incoming.model_dump(),)
            

            except (ValueError, ValidationError):
                await websocket.send_json({
                    "type": "error",
                    "sender": "user-123",
                    "content": "Invalid message format.",
                })
                continue

            await savedMessage(websocket, message, room_id, manager)

    except WebSocketDisconnect:
        logger.info("Client disconnected from room %s ", room_id)

    finally:
        manager.disconnection(websocket, room_id)



 