import logging

from fastapi import WebSocket

from app.db.message_delivery import persist_message_with_retry
from app.db.schemas.schemas import MessageEvent
from app.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


async def savedMessage( websocket: WebSocket ,message: MessageEvent, room_id: str, manager: ConnectionManager ) -> None:
    
    try:
        saved = await persist_message_with_retry(message, room_id)
    except Exception:
        logger.exception( "Unexpected error while saving message %s", message.id)
        saved = False

    
    if not saved:
        await websocket.send_json({
            "type": "error",
            "code": "message_persistence_failed",
            "content": (
                "Message could not be saved.",
                "Please try sending it again."
            ),
        })
        return False
    
    await manager.broadcast(message.model_dump(mode="json"), room_id)
    return True

