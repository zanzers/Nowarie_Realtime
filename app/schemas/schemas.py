from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field

class MessageEvent(BaseModel):
    type: Literal["chat.message"]
    sender: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=2000)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))