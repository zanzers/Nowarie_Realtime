
from unittest.mock import MagicMock, patch

import pytest

from app.db.message_repository import save_message
from tests.test_global import GLOBAL_TEST_MESSAGE
from app.db.schemas.schemas import MessageEvent


@pytest.fixture
def message():
    return MessageEvent(**GLOBAL_TEST_MESSAGE)


def make_existing_message(message, room_id):
    from uuid import UUID

    return MagicMock(
        id=UUID(hex=message.id),
        room_id=room_id,
        sender=message.sender,
        content=message.content,
        created_at=message.timestamp,
    )


def test_existing_matching_message_is_not_inserted(message):
    existing = make_existing_message(message, "conversation-1")

    mock_session = MagicMock()
    mock_session.scalar.return_value = existing

    with patch( "app.db.message_repository.SessionLocal") as mock_session_local:

        mock_session_local.return_value.__enter__.return_value = mock_session
        save_message(message, "conversation-1")


    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()


@pytest.mark.parametrize(
    "field, conflicting_value",
    [
        ("room_id", "conversation-2"),
        ("sender", "another-user"),
        ("content", "Different content"),
    ],
)

def test_existing_message_with_different_content_raises(message,field,conflicting_value):
    existing = make_existing_message(message, "conversation-1")
    setattr(existing, field, conflicting_value)

    mock_session = MagicMock()
    mock_session.scalar.return_value = existing

    with patch("app.db.message_repository.SessionLocal") as mock_session_local:
        mock_session_local.return_value.__enter__.return_value = mock_session

        with pytest.raises( ValueError, match="Message ID already exists with different content."):
            save_message(message, "conversation-1")

    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()


def test_existing_message_with_different_timestamp_raises(message):
    from datetime import timedelta

    existing = make_existing_message(message, "conversation-1")
    existing.created_at = message.timestamp + timedelta(seconds=1)

    mock_session = MagicMock()
    mock_session.scalar.return_value = existing

    with patch("app.db.message_repository.SessionLocal") as mock_session_local:
        mock_session_local.return_value.__enter__.return_value = mock_session

        with pytest.raises( ValueError, match="Message ID already exists with different content.",):
            save_message(message, "conversation-1")

    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()

