import pytest
import asyncio
from tests.test_lib import *
from app.main import app, manager
from starlette.websockets import WebSocket
from app.connection_manager import ConnectionManager
from unittest.mock import AsyncMock, patch
from starlette.websockets import WebSocketDisconnect
from tests.test_global import GLOBAL_TEST_MESSAGE, INVALID_MESSAGE, INVALID_ERROR, WEBSOCKET_CONNECT_ROOM, CLIENT_TIMESTAMP,CLIENT_OWN_ID,ERROR_MESSAGE

def test_connect_registers_connection():
    manager = ConnectionManager()
    websocket = AsyncMock()

    asyncio.run(manager.connect(websocket, "room-a"))

    websocket.accept.assert_awaited_once()
    assert websocket in manager.active_connections["room-a"]

def test_disconnection_removes_connection():
    manager = ConnectionManager()
    websocket = AsyncMock()

    manager.active_connections = {
        "room-a": [websocket]
    }

    manager.disconnection(websocket, "room-a")
    assert "room-a" not in manager.active_connections

def test_disconnection_preserves_other_connections():
    manager = ConnectionManager()
    
    websocket_a = AsyncMock()
    websocket_b = AsyncMock()

    manager.active_connections = {
        "room-a": [websocket_a, websocket_b]
    }
    manager.disconnection(websocket_a, "room-a")

    assert manager.active_connections["room-a"] == [websocket_b]

def test_disconnection_ignores_unknown_connection():
    manager = ConnectionManager()
    websocket = AsyncMock()

    manager.disconnection(websocket, "room-a")

    assert manager.active_connections == {}

def test_websocket_cleans_up_after_unexpected_error():
    with patch("app.main.is_room_member", return_value=True), patch(
        "app.main.savedMessage", new_callable=AsyncMock, side_effect=RuntimeError("Unexpected processing error")):
        with create_authenticated_client() as client:
           with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-1"]) as websocket:
            websocket.send_json(GLOBAL_TEST_MESSAGE)

            with pytest.raises(WebSocketDisconnect):
                websocket.receive_json()
    
    assert "conversation-1" not in manager.active_connections

def test_websocket_close_failure_logs_warning(caplog):
    original_close = WebSocket.close

    async def close_then_raise(websocket, code=1000, reason=None):
        await original_close(websocket, code=code, reason=reason)
        raise RuntimeError("WebSocket close failed")

    with patch( "app.main.is_room_member", return_value=True,), patch(
        "app.main.savedMessage", new_callable=AsyncMock, side_effect=RuntimeError("Unexpected processing error"),), patch(
        "starlette.websockets.WebSocket.close", new=close_then_raise,
    ):
        with create_authenticated_client() as client:
            with client.websocket_connect(
                WEBSOCKET_CONNECT_ROOM["conversation-1"]
            ) as websocket:
                websocket.send_json(GLOBAL_TEST_MESSAGE)

                with pytest.raises(WebSocketDisconnect):
                    websocket.receive_json()

    assert "Could not close Websocket" in caplog.text
    assert "conversation-1" not in manager.active_connections

def test_connect_does_not_register_connection_if_accept_fails():
    manager = ConnectionManager()
    websocket = AsyncMock()

    websocket.accept.side_effect = RuntimeError("Accept failed")

    with pytest.raises(RuntimeError, match="Accept failed"):
        asyncio.run(manager.connect(websocket, "room-a"))

    assert manager.active_connections == {}

def test_connect_registration_failure_does_not_leave_partial_state():
    manager = ConnectionManager()
    websocket = AsyncMock()

    class FailingConnections(dict):
        def __setitem__(self, key, value):
            raise RuntimeError("Registration failed")

    manager.active_connections = FailingConnections()

    with pytest.raises(RuntimeError, match="Registration failed"):
        asyncio.run(manager.connect(websocket, "room-a"))

    websocket.accept.assert_awaited_once()
    assert manager.active_connections == {}

def test_connect_registration_failure_preserves_existing_rooms():
    manager = ConnectionManager()

    existing_connection = AsyncMock()
    manager.active_connections = {
        "room-b": [existing_connection]
    }

    websocket = AsyncMock()

    class FailingConnections(dict):
        def __setitem__(self, key, value):
            raise RuntimeError("Registration failed")

    manager.active_connections = FailingConnections(
        manager.active_connections
    )

    with pytest.raises(RuntimeError, match="Registration failed"):
        asyncio.run(manager.connect(websocket, "room-a"))

    assert manager.active_connections["room-b"] == [existing_connection]
    assert "room-a" not in manager.active_connections

def test_disconnecting_one_client_preserves_other_clients():
    manager = ConnectionManager()

    websocket_a = AsyncMock()
    websocket_b = AsyncMock()

    manager.active_connections = {
        "room-a": [websocket_a, websocket_b]
    }

    manager.disconnection(websocket_a, "room-a")

    assert manager.active_connections["room-a"] == [websocket_b]
    assert websocket_a not in manager.active_connections["room-a"]
    assert websocket_b in manager.active_connections["room-a"]

def test_websocket_rejects_missing_token():
    with create_unauthenticated_client() as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["validation-test"]):
                pass
    
    assert exc_info.value.code == 1008
    assert exc_info.value.reason == "Authentication required."
       
def test_websocket_rejects_connection_when_jwt_config_is_missing(monkeypatch):
    monkeypatch.setattr("app.main.JWT_PUBLIC_KEY", None)

    with create_authenticated_client() as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["validation-test"]):
                pass

        assert exc_info.value.code == 1011
        assert exc_info.value.reason == "Server configuration error."

def test_websocket_rejects_invalid_token():
    with create_unauthenticated_client() as client:
        client.cookies.set("access_token", "invalid.jwt.token")

        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["validation-test"]):
                pass
        assert exc_info.value.code == 1008
        assert exc_info.value.reason == "Invalid access token."

def test_broadcast_removes_failed_connection():
    manager = ConnectionManager()

    failed_connection = AsyncMock()
    health_connection = AsyncMock()

    failed_connection.send_json.side_effect = RuntimeError("Connection failed")
    manager.active_connections = {
        "connection-test": [failed_connection, health_connection]
    }

    message = GLOBAL_TEST_MESSAGE

    asyncio.run(manager.broadcast(message, "connection-test"))
    
    assert failed_connection not in manager.active_connections["connection-test"]
    assert health_connection in manager.active_connections['connection-test']

    health_connection.send_json.assert_awaited_once_with(message)

def test_broadcast_does_not_send_to_other_rooms():

    manager = ConnectionManager()

    client_a = AsyncMock()
    client_b = AsyncMock()
    client_c = AsyncMock()

    manager.active_connections = {
        "room-a": [client_a, client_b],
        "room-b": [client_c],
    }
    message = GLOBAL_TEST_MESSAGE

    asyncio.run(manager.broadcast(message, "room-a"))

    client_a.send_json.assert_awaited_once_with(message)
    client_b.send_json.assert_awaited_once_with(message)
    client_c.send_json.assert_not_awaited()
