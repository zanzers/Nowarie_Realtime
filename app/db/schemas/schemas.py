from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict

class IncomingMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["chat.message"]
    content: str = Field(min_length=1, max_length=2000)
    

class MessageEvent(IncomingMessage):
    sender: str = Field(min_length=1, max_length=100)
    id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = Field( default_factory=lambda: datetime.now(timezone.utc))