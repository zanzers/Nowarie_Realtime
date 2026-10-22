from tests.test_global import GLOBAL_TEST_MESSAGE, INVALID_MESSAGE, INVALID_ERROR, WEBSOCKET_CONNECT_ROOM, CLIENT_TIMESTAMP,CLIENT_OWN_ID,ERROR_MESSAGE
import asyncio
from fastapi.testclient import TestClient
from app.main import app, manager
from unittest.mock import AsyncMock, patch

from app.connection_manager import ConnectionManager



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
                
def test_websocket_does_not_broadcast_when_persistence_fails():

    with patch("app.lib.lib_Main.persist_message_with_retry", new_callable=AsyncMock, return_value=False), patch("app.connection_manager.ConnectionManager.broadcast", new_callable=AsyncMock) as broadcast:
        with TestClient(app) as client:
            with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-1"]) as websocket_a:
                with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["conversation-1"]) as websocket_b:

                    websocket_a.send_json(GLOBAL_TEST_MESSAGE)

                    error = websocket_a.receive_json()
                    expected_error = {**ERROR_MESSAGE, "content": list(ERROR_MESSAGE["content"])}

                    assert error == expected_error

                    broadcast.assert_not_awaited()

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

# TIMESTAMP #####################################################

def test_websocket_generates_server_timestamp():
    with TestClient(app) as client:
        with client.websocket_connect(
            WEBSOCKET_CONNECT_ROOM["validation-test"]
        ) as websocket:
   
            websocket.send_json(GLOBAL_TEST_MESSAGE)
            response = websocket.receive_json()

            assert response["type"] == GLOBAL_TEST_MESSAGE["type"]
            assert response["sender"] == GLOBAL_TEST_MESSAGE["sender"]
            assert response["content"] == GLOBAL_TEST_MESSAGE["content"]
            assert "timestamp" in response
            assert response["timestamp"].endswith("+00:00") or response["timestamp"].endswith("Z")

def test_websocket_rejects_cliet_timestamp():
    with TestClient(app) as client:
        with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["validation-test"]) as websocket:
        
            websocket.send_json(CLIENT_TIMESTAMP)
            response = websocket.receive_json()

            assert response["type"] == "error"
            assert response["content"] == "Invalid message format." 


# MESSAGE ID #############################

def test_websocket_generate_server_message_id():
    with TestClient(app) as client:
        with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["validation-test"]) as websocket:
            
            websocket.send_json(GLOBAL_TEST_MESSAGE)
            response = websocket.receive_json()
            
            assert "id" in response
            assert len(response['id']) == 32
            assert all(character in "0123456789abcdef" for character in response["id"])

def test_websocket_rejects_client_message_id():
    with TestClient(app) as client:
        with client.websocket_connect( WEBSOCKET_CONNECT_ROOM["validation-test"]) as websocket:
        
            websocket.send_json(CLIENT_OWN_ID)
            response = websocket.receive_json()

            assert response["type"] == "error"
            assert response["content"] == "Invalid message format."

def test_websocket_generates_unique_message_ids():
    with TestClient(app) as client:
        with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["validation-test"]) as websocket:

            websocket.send_json(GLOBAL_TEST_MESSAGE)
            first_response = websocket.receive_json()

            second_message = {
                **GLOBAL_TEST_MESSAGE, 
                "content": "Second message",
            }

            websocket.send_json(second_message)
            second_response = websocket.receive_json()

            assert first_response["id"] != second_response["id"]


#  TEST MESSAGE ENDPOINT ###################

def test_get_room_messages_uses_requested_room():
    with patch("app.main.get_messages", return_value=[]) as mock_get_messages:
        with TestClient(app) as client:
            response = client.get("/rooms/conversation-2/messages?limit=20")
        
    assert response.status_code == 200
    mock_get_messages.assert_called_once_with(
        "conversation-2",
        20,
    )

def test_get_room_messages_return_history():
    with patch("app.main.get_messages", return_value=[]) as mock_get_messages:
        with TestClient(app) as client:
            response = client.get("/rooms/conversation-1/messages")
    
    assert response.status_code == 200
    assert response.json() == {
        "room_id": "conversation-1",
        "messages": [],
    }
    mock_get_messages.assert_called_once_with("conversation-1", 50)

def test_get_room_messages_respects_limit():
    with patch("app.main.get_messages", return_value=[], ) as mock_get_messages:
        with TestClient(app) as client:
            response = client.get("/rooms/conversation-1/messages?limit=10")
    
    print("Status:", response.status_code)
    print("Status:", response.json())
    
    assert response.status_code == 200
    mock_get_messages.assert_called_once_with(
        "conversation-1",
        10,
    )
    
def test_get_room_messages_rejects_invalid_limit():
    with TestClient(app) as client:
        response = client.get("/rooms/conversation-1/messages?limit=0")
    assert response.status_code == 422

