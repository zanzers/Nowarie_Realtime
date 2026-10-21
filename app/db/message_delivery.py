import asyncio
import logging
from fastapi.concurrency import run_in_threadpool

from app.db.message_repository import save_message
from app.db.schemas.schemas import MessageEvent


logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
RETRY_DELAY = 1

async def persist_message_with_retry(message: MessageEvent, room_id: str) -> bool:

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            await run_in_threadpool(save_message, message, room_id)
            return True
            
        except Exception :
            logger.exception("Failed to persist message %s (attempt %s %s)", message.id, attempt, MAX_ATTEMPTS,)
            
            if attempt == MAX_ATTEMPTS:
                return False
            
            delay = RETRY_DELAY * (2 ** (attempt - 1))
            await asyncio.sleep(delay)

    
    return False



