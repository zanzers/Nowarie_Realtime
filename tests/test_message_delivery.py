import pytest
import logging
from unittest.mock import AsyncMock, patch

from app.db.message_delivery import persist_message_with_retry, MAX_ATTEMPTS
from app.db.schemas.schemas import MessageEvent
from tests.test_global import GLOBAL_TEST_MESSAGE

@pytest.fixture
def message(): return MessageEvent(**GLOBAL_TEST_MESSAGE, sender="user-123")

@pytest.mark.asyncio
async def test_message_persisted_succeeds_on_first_attempt(message):
    with patch("app.db.message_delivery.run_in_threadpool", new_callable=AsyncMock) as save:
        
        result = await persist_message_with_retry(message, "conversation-1")
        assert result is True
        save.assert_awaited_once()

@pytest.mark.asyncio
async def test_persisted_retries_and_then_succeeds(message):
    with (patch("app.db.message_delivery.run_in_threadpool", new_callable=AsyncMock, side_effect=[RuntimeError("Temporary database failure"), None],
        ) as save, patch("app.db.message_delivery.asyncio.sleep", new_callable=AsyncMock) as sleep,
        ):
        result = await persist_message_with_retry(message, "conversation-1")

        assert result is True
        assert save.await_count == 2
        sleep.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_persisted_return_false_after_all_attempts(message):
    with(patch("app.db.message_delivery.run_in_threadpool", new_callable=AsyncMock, side_effect=RuntimeError("Database unavailable"), ) as save,
        patch("app.db.message_delivery.asyncio.sleep", new_callable=AsyncMock) as sleep, 
        ):
        result = await persist_message_with_retry(message, "conversation-1")
        
    assert result is None
    assert save.await_count == MAX_ATTEMPTS
    assert [call.args[0] for call in sleep.await_args_list] == [1, 2, 4, 8]

@pytest.mark.asyncio
async def test_returns_false_when_no_attempts_configured(message):
    with patch("app.db.message_delivery.MAX_ATTEMPTS", 0):
        result = await persist_message_with_retry(message, "conversation-1")

    assert result is None