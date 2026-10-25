import pytest
from unittest.mock import AsyncMock, patch

from app.db.schemas.schemas import MessageEvent
from tests.test_global import GLOBAL_TEST_MESSAGE, ERROR_MESSAGE
from app.connection_manager import ConnectionManager
from app.services.message_service import process_incoming_message
from app.db.message_delivery import persist_message_with_retry
from app.type.global_Type import INVALID_MESSAGE_ERROR, PERSISTENCE_ERROR
from app.services.message_service import Broadcaster

PERSIST = "app.services.message_service.persist_message_with_retry"


@pytest.fixture
def message(): return MessageEvent(**GLOBAL_TEST_MESSAGE, sender="sender-123")

def test_connection_manager_implements_broadcaster_protocol():
    manager = ConnectionManager()

    assert isinstance(manager, Broadcaster)


@pytest.mark.asyncio
async def test_broadcaster_can_broadcast_asynchronously():
    broadcaster = AsyncMock(spec=Broadcaster)

    await broadcaster.broadcast(
        {"type": "chat.message", "content": "Hello!"},
        "conversation-1",
    )

    broadcaster.broadcast.assert_awaited_once_with(
        {"type": "chat.message", "content": "Hello!"},
        "conversation-1",
    )

@pytest.mark.asyncio
async def test_valid_message_is_saved_and_broadcast():
    broadcaster = AsyncMock(spec=ConnectionManager)
    saved = MessageEvent(**GLOBAL_TEST_MESSAGE, sender="sender-123")

    with patch(PERSIST, new_callable=AsyncMock, return_value=saved) as persist:
        result = await process_incoming_message(
            GLOBAL_TEST_MESSAGE, "sender-123", "conversation-1", broadcaster
        )

    assert result.ok is True
    assert result.event is saved
    built_message, room_id = persist.await_args.args
    assert built_message.sender == "sender-123"
    assert room_id == "conversation-1"
    broadcaster.broadcast.assert_awaited_once_with(
        saved.model_dump(mode="json"), "conversation-1"
    )

@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    {"type": "chat.message", "content": ""},
    {**GLOBAL_TEST_MESSAGE, "sender": "someone-else"},
    {**GLOBAL_TEST_MESSAGE, "id": "my-own-id"},
    {**GLOBAL_TEST_MESSAGE, "timestamp": "2020-01-01T00:00:00Z"},
    ["not", "a", "dict"],
])
async def test_invalid_payload_is_rejected_without_saving(payload):
    broadcaster = AsyncMock(spec=ConnectionManager)

    with patch(PERSIST, new_callable=AsyncMock) as persist:
        result = await process_incoming_message(payload, "sender-123", "conversation-1", broadcaster)

    assert result.ok is False
    assert result.error == INVALID_MESSAGE_ERROR
    persist.assert_not_awaited()
    broadcaster.broadcast.assert_not_awaited()


@pytest.mark.asyncio
async def test_failed_persistence_returns_error_without_broadcast():
    broadcaster = AsyncMock(spec=ConnectionManager)

    with patch(PERSIST, new_callable=AsyncMock, return_value=None):
        result = await process_incoming_message(
            GLOBAL_TEST_MESSAGE, "sender-123", "conversation-1", broadcaster
        )

    assert result.ok is False
    assert result.error == PERSISTENCE_ERROR
    broadcaster.broadcast.assert_not_awaited()


@pytest.mark.asyncio
async def test_unexpected_persistence_exception_returns_error_without_broadcast():
    broadcaster = AsyncMock(spec=ConnectionManager)

    with patch(PERSIST, new_callable=AsyncMock, side_effect=RuntimeError("boom")):
        result = await process_incoming_message(
            GLOBAL_TEST_MESSAGE, "sender-123", "conversation-1", broadcaster
        )

    assert result.ok is False
    assert result.error == PERSISTENCE_ERROR
    broadcaster.broadcast.assert_not_awaited()

@pytest.mark.asyncio
async def test_persist_returns_the_message_from_save(message):
    with patch("app.db.message_delivery.save_message", return_value=message):
        result = await persist_message_with_retry(message, "conversation-1")

    assert result is message
    assert not isinstance(result, bool)


@pytest.mark.asyncio
async def test_unexpected_persistence_exception_returns_error_without_broadcast():
    broadcaster = AsyncMock(spec=ConnectionManager)
    with patch(PERSIST, new_callable=AsyncMock, side_effect=RuntimeError("Unexpected database error")) as persist:
        result = await process_incoming_message(
            GLOBAL_TEST_MESSAGE,
            "sender-123",
            "conversation-1",
            broadcaster,
        )
    assert result.ok is False
    assert result.error == PERSISTENCE_ERROR
    persist.assert_awaited_once()
    broadcaster.broadcast.assert_not_awaited()

