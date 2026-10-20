from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class IncomingMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["chat.message"]
    sender: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=2000)
    

class MessageEvent(IncomingMessage):
    timestamp: datetime = Field( default_factory=lambda: datetime.now(timezone.utc))