import asyncio
from fastapi.testclient import TestClient
from app.main import app, manager
from unittest.mock import AsyncMock

from app.connection_manager import ConnectionManager
from tests.test_global import GLOBAL_TEST_MESSAGE, INVALID_MESSAGE, INVALID_ERROR, WEBSOCKET_CONNECT_ROOM





def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")

    
    assert response.status_code == 200
    assert response.json() == {
        "status":"Healthy",
        "service": "nowarie-realtime",
        "version":"0.1.0" 
    }


def test_websocket_rooms_are_separated():
    with TestClient(app) as client:
        with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-1"]) as websocket_a: 
            with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-2"]) as websocket_b:

                assert "conversation-1" in manager.active_connections
                assert "conversation-2" in manager.active_connections

                assert len( manager.active_connections["conversation-1"]) == 1
                assert len( manager.active_connections["conversation-2"]) == 1


def test_websocket_broadcast_within_room():
    with TestClient(app) as client:
        with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-1"]) as websocket_a:
            with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-1"]) as websocket_b:
                
                

                websocket_a.send_json(GLOBAL_TEST_MESSAGE)

                response_a = websocket_a.receive_json()
                response_b = websocket_b.receive_json()

                assert response_a["type"] == GLOBAL_TEST_MESSAGE["type"]
                assert response_a["sender"] == GLOBAL_TEST_MESSAGE["sender"]
                assert response_a["content"] == GLOBAL_TEST_MESSAGE["content"]
                assert "timestamp" in response_a

                assert response_b == response_a
                


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


def test_websocket_rejects_invalid_message():
    with TestClient(app) as client:
        with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["validation-test"]) as websocket:
            websocket.send_json(INVALID_MESSAGE)

            response = websocket.receive_json()

            assert response == INVALID_ERROR


    