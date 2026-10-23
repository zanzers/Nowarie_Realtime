import pytest
import asyncio
from tests.test_lib import *
from app.main import app, manager
from fastapi.testclient import TestClient
from app.connection_manager import ConnectionManager
from unittest.mock import AsyncMock, patch
from starlette.websockets import WebSocketDisconnect
from tests.test_global import GLOBAL_TEST_MESSAGE, INVALID_MESSAGE, INVALID_ERROR, WEBSOCKET_CONNECT_ROOM, CLIENT_TIMESTAMP,CLIENT_OWN_ID,ERROR_MESSAGE


@patch("app.main.is_room_member", return_value=True)
def test_websocket_rooms_are_separated(mock_is_room_member):
    with create_authenticated_client() as client:
        with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-1"]) as websocket_a: 
            with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-2"]) as websocket_b:

                websocket_a.send_json(GLOBAL_TEST_MESSAGE)
                response_a = websocket_a.receive_json()

                assert response_a["type"] == GLOBAL_TEST_MESSAGE["type"]
                assert response_a["sender"] == "user-123"
                assert response_a["content"] == GLOBAL_TEST_MESSAGE["content"]

                websocket_b.send_json({
                    "type": "chat.message",
                    "content": "Message from conversation-2"
                })
                response_b = websocket_b.receive_json()

                assert response_b["content"] == "Message from conversation-2"
                assert response_b["sender"] == "user-123"

@patch("app.main.is_room_member", return_value=True)
def test_websocket_broadcast_within_room(mock_is_room_member):
    with TestClient(app) as client:

        token = create_test_token()
        client.cookies.set("access_token", token)

        with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-1"]) as websocket_a:
            with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-1"]) as websocket_b:
                
                

                websocket_a.send_json(GLOBAL_TEST_MESSAGE)

                response_a = websocket_a.receive_json()
                response_b = websocket_b.receive_json()

                assert response_a["type"] == GLOBAL_TEST_MESSAGE["type"]
                assert response_a["sender"] == "user-123"
                assert response_a["content"] == GLOBAL_TEST_MESSAGE["content"]
                assert "timestamp" in response_a
                assert response_b == response_a

@patch("app.main.is_room_member", return_value=True)     
def test_websocket_does_not_broadcast_when_persistence_fails(mock_is_room_member):

    with patch("app.lib.lib_Main.persist_message_with_retry", new_callable=AsyncMock, return_value=False), patch("app.connection_manager.ConnectionManager.broadcast", new_callable=AsyncMock) as broadcast:
        with create_authenticated_client() as client:
            with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-1"]) as websocket_a:
                with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-1"]) as websocket_b:

                    websocket_a.send_json(GLOBAL_TEST_MESSAGE)

                    error = websocket_a.receive_json()
                    expected_error = {**ERROR_MESSAGE, "content": list(ERROR_MESSAGE["content"])}

                    assert error == expected_error

                    broadcast.assert_not_awaited()

@patch("app.main.is_room_member", return_value=True)  
def test_websocket_rejects_invalid_message(mock_is_room_member):
    with create_authenticated_client() as client:
        with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["validation-test"]) as websocket:
            websocket.send_json(INVALID_MESSAGE)

            response = websocket.receive_json()

            assert response == INVALID_ERROR

@patch("app.main.is_room_member", return_value=True)  
def test_websocket_allows_room_member(mock_is_room_member):
    with create_authenticated_client() as client:
        with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-1"]) as websocket:
            websocket.send_json(GLOBAL_TEST_MESSAGE)
            response = websocket.receive_json()

            assert response["type"] == GLOBAL_TEST_MESSAGE["type"]
            assert response["sender"] == "user-123"

    mock_is_room_member.assert_called_once_with("conversation-1", "user-123")

@patch("app.main.is_room_member", return_value=False)  
def test_websocket_rejects_non_member(mock_is_room_member):
    with create_authenticated_client() as client:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-1"]): pass

    mock_is_room_member.assert_called_once_with("conversation-1", "user-123")

@patch("app.main.is_room_member", side_effect=RuntimeError("Database unavailable"))  
def test_websocket_rejects_when_room_check_fails(mock_is_room_member):
    with create_authenticated_client() as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-1"]): pass

    assert exc_info.value.code == 1011

    mock_is_room_member.assert_called_once_with("conversation-1", "user-123")


