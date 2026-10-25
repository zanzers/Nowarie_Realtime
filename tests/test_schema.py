import pytest
from pydantic import ValidationError
from app.db.schemas.schemas import IncomingMessage

def test_incoming_message_accepts_client_message_id():
    msg = IncomingMessage(type="chat.message", content="hi", client_message_id="abc")
    assert msg.client_message_id == "abc"

@pytest.mark.parametrize("bad", ["", "x" * 65])
def test_incoming_message_rejects_bad_client_message_id(bad):
    with pytest.raises(ValidationError):
        IncomingMessage(type="chat.message", content="hi", client_message_id=bad)