import pytest
from unittest.mock import AsyncMock, patch

from app.db.schemas.schemas import MessageEvent
from tests.test_global import GLOBAL_TEST_MESSAGE, ERROR_MESSAGE
from app.connection_manager import ConnectionManager
from app.lib.lib_Main import savedMessage
from app.db.message_delivery import persist_message_with_retry


@pytest.fixture
def message(): return MessageEvent(**GLOBAL_TEST_MESSAGE)

@pytest.mark.asyncio
async def test_saved_message_broadcasts_after_success(message):
    websocket = AsyncMock()
    manager = AsyncMock(spec=ConnectionManager)

    with patch("app.lib.lib_Main.persist_message_with_retry", new_callable=AsyncMock, return_value=True,):
        result = await savedMessage(websocket, message, "conversation-1", manager)
    
    assert result is True
    websocket.send_json.assert_not_awaited()
    manager.broadcast.assert_awaited_once_with(message.model_dump(mode="json"), "conversation-1")


@pytest.mark.asyncio
async def test_failed_persistence_sends_error_without_broadcast(message):
    websocket = AsyncMock()
    manager = AsyncMock(spec=ConnectionManager)

    with patch("app.lib.lib_Main.persist_message_with_retry", new_callable=AsyncMock, return_value=False):
        result = await savedMessage(websocket, message, "conversation-1", manager)
    
    assert result is False
    websocket.send_json.assert_awaited_once_with({ **ERROR_MESSAGE })
    manager.broadcast.assert_not_awaited()


@pytest.mark.asyncio
async def test_unexpected_persistence_exception_sends_error_without_broadcast(message):
    websocket = AsyncMock()
    manager = AsyncMock(spec=ConnectionManager)
    
    with patch("app.lib.lib_Main.persist_message_with_retry", new_callable=AsyncMock, side_effect=RuntimeError("Unexpected database error"),
        ):
        result = await savedMessage(websocket, message, "comversation-1", manager)
        
    assert result is False
    
    websocket.send_json.assert_awaited_once_with({ **ERROR_MESSAGE })
    manager.broadcast.assert_not_awaited()