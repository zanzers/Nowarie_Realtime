import pytest
import uuid

from unittest.mock import MagicMock, patch


from tests.test_global import GLOBAL_TEST_MESSAGE
from app.db.schemas.schemas import MessageEvent
from datetime import datetime, timezone
from app.db.message_repository import save_message, get_messages, get_messages_after, UnknownMessageError, _to_event


@pytest.fixture
def message():
    return MessageEvent(**GLOBAL_TEST_MESSAGE, sender="user-123")



def make_message(room_id, sender, content, created_at):
    return MagicMock(
        id=uuid.uuid4(),
        room_id=room_id,
        sender=sender,
        content=content,
        created_at=created_at,
    )


def make_existing_message(message, room_id):
    from uuid import UUID

    return MagicMock(
        id=UUID(hex=message.id),
        room_id=room_id,
        sender=message.sender,
        content=message.content,
        created_at=message.timestamp,
    )


def test_get_message_chronological_order():
    older = make_message(
        "conversation-1",
        "alice",
        "First message",
        datetime(2026, 10, 21, 10, 0, tzinfo=timezone.utc),
    )
    newer = make_message(
        "conversation-1",
        "bob",
        "Second message",
        datetime(2026, 10, 21, 10, 1, tzinfo=timezone.utc)
    )

    session = MagicMock()
    session.scalars.return_value.all.return_value = [newer, older]

    with patch("app.db.message_repository.SessionLocal") as session_local:
        session_local.return_value.__enter__.return_value = session

        messages = get_messages("conversation-1")

    assert [message.content for message in messages] == ["First message", "Second message"]    

def test_get_messages_returns_empty_list():

    session = MagicMock()
    session.scalars.return_value.all.return_value = []

    with patch("app.db.message_repository.SessionLocal") as session_local:
        session_local.return_value.__enter__.return_value = session

        messages = get_messages("empty-room")

    assert messages == []

def test_get_messages_uses_requested_limit():
    session = MagicMock()
    session.scalars.return_value.all.return_value = []

    with patch("app.db.message_repository.SessionLocal") as session_local:
        session_local.return_value.__enter__.return_value = session

        get_messages("conversation-1", limit=10)
    
    statement = session.scalars.call_args.args[0]
    assert statement._limit_clause.value == 10

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


def test_get_messages_after_filters_and_orders_by_seq():
    session = MagicMock()
    session.scalar.return_value = 42
    session.scalars.return_value.all.return_value = []
    with patch("app.db.message_repository.SessionLocal") as session_local:
        session_local.return_value.__enter__.return_value = session
        get_messages_after("conversation-1", "a" * 32, limit=10)
    statement = session.scalars.call_args.args[0]
    assert "seq >" in str(statement)
    assert statement._limit_clause.value == 10

def test_get_messages_after_unknown_cursor_raises():
    session = MagicMock()
    session.scalar.return_value = None
    with patch("app.db.message_repository.SessionLocal") as session_local:
        session_local.return_value.__enter__.return_value = session
        with pytest.raises(UnknownMessageError):
            get_messages_after("conversation-1", "a" * 32)

def test_to_event_maps_database_row_to_message_event():
    message_id = uuid.uuid4()
    created_at = datetime(2026, 10, 24, 10, 0, tzinfo=timezone.utc)
    row = make_message("conversation-1", "alice", "Hello!", created_at)
    row.id = message_id

    event = _to_event(row)

    assert event.type == "chat.message"
    assert event.id == message_id.hex
    assert event.sender == "alice"
    assert event.content == "Hello!"
    assert event.timestamp == created_at


def test_to_event_serializes_id_as_32_char_hex():
    row = make_message(
        "conversation-1", "alice", "Hi",
        datetime(2026, 10, 24, 10, 0, tzinfo=timezone.utc),
    )

    payload = _to_event(row).model_dump(mode="json")

    assert len(payload["id"]) == 32
    assert "-" not in payload["id"]