import uuid
from app.main import app, manager
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import patch
from app.core.security import AuthenticationError
from tests.test_global import GLOBAL_TEST_MESSAGE,  WEBSOCKET_CONNECT_ROOM ,CLIENT_OWN_ID

from app.db.message_repository import UnknownMessageError


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
    with patch("app.main.is_room_member", return_value=True), \
     patch("app.main.get_messages", return_value=[]) as mock_get_messages:
        with create_authenticated_client() as client:
            response = client.get("/rooms/conversation-2/messages?limit=20")
        
    assert response.status_code == 200
    mock_get_messages.assert_called_once_with(
        "conversation-2",
        20,
    )

def test_get_room_messages_return_history():
    with patch("app.main.is_room_member", return_value=True), \
     patch("app.main.get_messages", return_value=[]) as mock_get_messages:

        with create_authenticated_client() as client:
            response = client.get("/rooms/conversation-1/messages")
    
    assert response.status_code == 200
    assert response.json() == {
        "room_id": "conversation-1",
        "messages": [],
    }
    mock_get_messages.assert_called_once_with("conversation-1", 50)

def test_get_room_messages_respects_limit():
    with patch("app.main.is_room_member", return_value=True), \
      patch("app.main.get_messages", return_value=[], ) as mock_get_messages:
        with create_authenticated_client() as client:
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

def test_get_room_messages_rejects_non_member():
    with patch("app.main.is_room_member", return_value=False), \
         patch("app.main.get_messages") as mock_get_messages:

        with create_authenticated_client() as client:
            response = client.get( "/rooms/conversation-1/messages")

    assert response.status_code == 403
    assert response.json() == { "detail": "You are not a member of this room."}

    mock_get_messages.assert_not_called()

def test_authenticated_user_rejects_missing_token():
    with TestClient(app) as client:
        response = client.get( "/rooms/conversation-1/messages")

    assert response.status_code == 401
    assert response.json() == { "detail": "Authentication required."}

def test_authenticated_user_rejects_missing_jwt_config():
    with patch("app.core.security.JWT_PUBLIC_KEY", None), \
         TestClient(app) as client:

        client.cookies.set("access_token", "test-token")
        response = client.get("/rooms/conversation-1/messages")

    assert response.status_code == 500
    assert response.json() == { "detail": "Server configuration error."}




def test_authenticated_user_rejects_invalid_token():
    with patch( "app.core.security.verify_access_token", side_effect=AuthenticationError("Invalid token"),), \
        TestClient(app) as client:

        client.cookies.set("access_token", "invalid-token")
        response = client.get( "/rooms/conversation-1/messages")

    assert response.status_code == 401
    assert response.json() == { "detail": "Invalid access token."}



def test_authenticated_user_rejects_missing_subject():
    with patch( "app.core.security.verify_access_token", return_value={"iss": "nowarie-realtime"}), \
         TestClient(app) as client:

         client.cookies.set("access_token", "test-token")
         response = client.get("/rooms/conversation-1/messages")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid access token."}


def test_authenticated_user_returns_subject():
    with patch( "app.core.security.verify_access_token", return_value={"sub": "user-123"}), \
         patch("app.main.is_room_member", return_value=True), \
         patch("app.main.get_messages", return_value=[]), \
         TestClient(app) as client:

        client.cookies.set("access_token", "test-token")
        response = client.get( "/rooms/conversation-1/messages")

    assert response.status_code == 200


def test_get_room_messages_after_id_uses_cursor():
    with patch("app.main.is_room_member", return_value=True), \
         patch("app.main.get_messages_after", return_value=[]) as mock_after:
        with create_authenticated_client() as client:
            response = client.get(f"/rooms/conversation-1/messages?after_id={'a'*32}&limit=20")
    assert response.status_code == 200
    mock_after.assert_called_once_with("conversation-1", "a" * 32, 20)

def test_get_room_messages_after_unknown_id_returns_404():
    with patch("app.main.is_room_member", return_value=True), \
         patch("app.main.get_messages_after", side_effect=UnknownMessageError("x")):
        with create_authenticated_client() as client:
            response = client.get(f"/rooms/conversation-1/messages?after_id={'a'*32}")
    assert response.status_code == 404

def test_get_room_messages_after_rejects_malformed_id():
    with create_authenticated_client() as client:
        response = client.get("/rooms/conversation-1/messages?after_id=not-hex")
    assert response.status_code == 422

def test_get_room_messages_after_id_rejects_non_member():
    with patch("app.main.is_room_member", return_value=False), \
         patch("app.main.get_messages_after") as mock_after:
        with create_authenticated_client() as client:
            response = client.get(f"/rooms/conversation-1/messages?after_id={'a'*32}")
    assert response.status_code == 403
    mock_after.assert_not_called()



@patch("app.main.is_room_member", return_value=True)
def test_websocket_echoes_client_message_id(mock_is_room_member):
    payload = {**GLOBAL_TEST_MESSAGE, "client_message_id": uuid.uuid4().hex}
    with create_authenticated_client() as client:
        with client.websocket_connect(WEBSOCKET_CONNECT_ROOM["validation-test"]) as websocket:
            websocket.send_json(payload)
            response = websocket.receive_json()
    assert response["client_message_id"] == payload["client_message_id"]