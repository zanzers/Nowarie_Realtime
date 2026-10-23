import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Request, HTTPException
from pydantic import ValidationError

from app.lib.lib_Main import savedMessage
from app.connection_manager import ConnectionManager
from app.db.schemas.schemas import MessageEvent, IncomingMessage
from app.core.config import ( JWT_PUBLIC_KEY, JWT_ISSUER, JWT_AUDIENCE )
from app.core.security import ( AuthenticationError, verify_access_token, authenticated_user )
from app.db.message_repository import get_messages
from app.db.room_repository import is_room_member


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
async def get_room_messages(room_id: str, request: Request, limit: int = Query(default=50, ge=1, le=100)):

    authenticated_user_id = authenticated_user(request)

    if not is_room_member(room_id, authenticated_user_id):
        raise HTTPException( status_code=403, detail="You are not a member of this room.")


    messages = get_messages(room_id, limit)
    return {
        "room_id": room_id,
        "messages": messages,
    }





@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, room_id: str):

    token = websocket.cookies.get("access_token")

    if not token:
        await websocket.close(
            code=1008, 
            reason="Authentication required.")
        return
    
    if not JWT_PUBLIC_KEY or not JWT_ISSUER or not JWT_AUDIENCE:
        logger.error("JWT configuration is missing.")
        await websocket.close(
            code=1011,
            reason="Server configuration error.")
        return
    
    try:
        claims = verify_access_token(token, public_key=JWT_PUBLIC_KEY, issuer=JWT_ISSUER, audience=JWT_AUDIENCE)
    except AuthenticationError as exc:
        logger.warning("Authentication error: %s", exc)
        await websocket.close(code=1008, reason="Invalid access token.")
        return
    
    authenticated_user_id = claims["sub"]

    try:
        allowed = is_room_member(room_id, authenticated_user_id)
    except Exception:
        logger.exception("Failed to check room membership for user %s in room %s", authenticated_user_id, room_id)

        await websocket.close(code=1011, reason="Server error while checking room access.")
        return
    
    if not allowed:
        await websocket.close(code=1008, reason="You are not a member of this room.")
        return


    await manager.connect(websocket, room_id)
    logger.info("Authenticated user %s connected to room %s", authenticated_user_id, room_id)



    try:
        while True:
            try:
                payload = await websocket.receive_json()
                incoming = IncomingMessage.model_validate(payload)
                message = MessageEvent(**incoming.model_dump(),sender=authenticated_user_id)
            

            except (ValueError, ValidationError):
                await websocket.send_json({
                    "type": "error",
                    "code": "invalid_message",
                    "content": "Invalid message format.",
                })
                continue

            await savedMessage(websocket, message, room_id, manager)

    except WebSocketDisconnect:
        logger.info("User %s disconnected from room %s ",authenticated_user_id, room_id)

    except Exception:
        logger.exception("Unexpected Websocket error for user %s in room %s", authenticated_user_id, room_id)

    try:
        await websocket.close(code=1011, reason="Internal server error.")
    except Exception:
        logger.warning("Could not close Websocket for user %s in room %s", authenticated_user_id, room_id)

    finally:
        manager.disconnection(websocket, room_id)



 