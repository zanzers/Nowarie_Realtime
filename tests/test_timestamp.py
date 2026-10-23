from app.main import app
from unittest.mock import patch
from tests.test_global import GLOBAL_TEST_MESSAGE, CLIENT_TIMESTAMP, WEBSOCKET_CONNECT_ROOM
from tests.test_main import create_authenticated_client



# TIMESTAMP #####################################################

@patch("app.main.is_room_member", return_value=True)  
def test_websocket_generates_server_timestamp(mock_is_room_member):
    with create_authenticated_client() as client:
        with client.websocket_connect(
            WEBSOCKET_CONNECT_ROOM["validation-test"]
        ) as websocket:
   
            websocket.send_json(GLOBAL_TEST_MESSAGE)
            response = websocket.receive_json()

            assert response["type"] == GLOBAL_TEST_MESSAGE["type"]
            assert response["sender"] == "user-123"
            assert response["content"] == GLOBAL_TEST_MESSAGE["content"]
            assert "timestamp" in response
            assert response["timestamp"].endswith("+00:00") or response["timestamp"].endswith("Z")

@patch("app.main.is_room_member", return_value=True)  
def test_websocket_rejects_cliet_timestamp(mock_is_room_member):
    with create_authenticated_client() as client:
        with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["validation-test"]) as websocket:
        
            websocket.send_json(CLIENT_TIMESTAMP)
            response = websocket.receive_json()

            assert response["type"] == "error"
            assert response["content"] == "Invalid message format." 