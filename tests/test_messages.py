
from app.main import app, manager
from fastapi.testclient import TestClient
from unittest.mock import patch
from tests.test_global import GLOBAL_TEST_MESSAGE,  WEBSOCKET_CONNECT_ROOM ,CLIENT_OWN_ID

from tests.test_lib import *



# MESSAGE ID #############################

@patch("app.main.is_room_member", return_value=True)  
def test_websocket_generate_server_message_id(mock_is_room_member):
    with create_authenticated_client() as client:
        with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["validation-test"]) as websocket:
            
            websocket.send_json(GLOBAL_TEST_MESSAGE)
            response = websocket.receive_json()
            
            assert "id" in response
            assert len(response['id']) == 32
            assert all(character in "0123456789abcdef" for character in response["id"])

@patch("app.main.is_room_member", return_value=True)  
def test_websocket_rejects_client_message_id(mock_is_room_member):
    with create_authenticated_client() as client:
        with client.websocket_connect( WEBSOCKET_CONNECT_ROOM["validation-test"]) as websocket:
        
            websocket.send_json(CLIENT_OWN_ID)
            response = websocket.receive_json()

            assert response["type"] == "error"
            assert response["content"] == "Invalid message format."

@patch("app.main.is_room_member", return_value=True)  
def test_websocket_generates_unique_message_ids(mock_is_room_member):
    with create_authenticated_client() as client:
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
