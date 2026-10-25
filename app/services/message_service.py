import logging
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from pydantic import ValidationError
from app.db.message_delivery import persist_message_with_retry
from app.db.schemas.schemas import IncomingMessage, MessageEvent
from app.type.global_Type import INVALID_MESSAGE_ERROR, PERSISTENCE_ERROR

logger = logging.getLogger(__name__)

@runtime_checkable
class Broadcaster(Protocol):
    async def broadcast(self, message: dict, room_id: str) -> None:
        ...

@dataclass(frozen=True)
class SendReult:
    event: MessageEvent | None = None
    error: dict | None = None

    @property
    def ok(self) -> bool:
        return self.event is not None


async def process_incoming_message(payload: dict, sender_id: str, room_id: str, broadcast: Broadcaster) -> SendReult:
    try:

        incoming = IncomingMessage.model_validate(payload)
        message = MessageEvent(**incoming.model_dump(), sender=sender_id)
    except (ValueError, ValidationError) as exc:
        logger.warning("Rejected invalid message from %s in room %s: %s", sender_id, room_id, exc)
        return SendReult(error=INVALID_MESSAGE_ERROR)

    try: 
        saved = await persist_message_with_retry(message, room_id)
    except Exception:
        logger.exception(
            "Unexpected error while saving message %s",
            message.id
        )
        saved = None
    
    if saved is None:
        return SendReult(error=PERSISTENCE_ERROR)
    
    await broadcast.broadcast(saved.model_dump(mode="json"), room_id)
    return SendReult(event=saved)