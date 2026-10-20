from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.connection_manager import ConnectionManager
from pydantic import ValidationError
from app.schemas.schemas import MessageEvent, IncomingMessage


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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
   
    await manager.connect(websocket, room_id)
    print(f"Client connected to the room {room_id}")

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

            await manager.broadcast(message.model_dump(mode="json"), room_id)

    except WebSocketDisconnect:
        print(f"Client disconnected from room {room_id}. ")

    finally:
        manager.disconnection(websocket, room_id)



 