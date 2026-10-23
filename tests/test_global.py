








GLOBAL_TEST_MESSAGE = {
    "type": "chat.message",
    "content": "Hello nowarie"
}

INVALID_MESSAGE = {
    "type": "chat.message",
    "content": "",
}

INVALID_ERROR = {
    "type": "error",
    "code": "invalid_message",
    "content": "Invalid message format.",
}


WEBSOCKET_CONNECT_ROOM ={
    "conversation-1": "/ws?room_id=conversation-1",
    "conversation-2": "/ws?room_id=conversation-2",
    "conversation-3": "/ws?room_id=conversation-3",
    "validation-test": "/ws?room_id=validation-test",
}

CLIENT_TIMESTAMP = {
    "type": "chat.message",
    "sender": "user-123",
    "content": "Hello Nowarie",
    "timestamp": "2020-01-01T00:00:00Z",
}

CLIENT_OWN_ID  ={
    "type": "chat.message",
    "sender": "user-123",
    "content": "Hello Nowarie",
    "id": "my-custom-message-id",
}

ERROR_MESSAGE = {
    "type": "error", 
    "code": "message_persistence_failed", 
    "content": ( 
        "Message could not be saved.",
        "Please try sending it again." 
    ),
}