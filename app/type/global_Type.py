

INVALID_MESSAGE_ERROR = {
    "type": "error",
    "code": "invalid_message",
    "content": "Invalid message format.", 
}

PERSISTENCE_ERROR = {
    "type": "error",
    "code": "message_persistence_failed",
    "content": (
        "Message could not be saved.",
        "Please try sending it again.",
    ), 
}