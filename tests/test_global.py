GLOBAL_TEST_MESSAGE = {
    "type": "chat.message",
    "sender": "user-123",
    "content": "Hello nowarie"
}

INVALID_MESSAGE = {
    "type": "chat.message",
    "content": "Invalid message format.",
}

INVALID_ERROR = {
    "type": "error",
    "sender": "user-123",
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