from unittest.mock import MagicMock, patch

from app.db.room_repository import is_room_member

@patch("app.db.room_repository.SessionLocal")
def test_user_is_room_member(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_session

    mock_session.scalar.return_value = object()
    result = is_room_member("room-abc", "user-123")

    assert result is True
    mock_session.scalar.assert_called_once()

@patch("app.db.room_repository.SessionLocal")
def test_user_is_not_room_member(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_session

    mock_session.scalar.return_value = None

    result = is_room_member("room-abc", "user-999")

    assert result is False
    mock_session.scalar.assert_called_once()