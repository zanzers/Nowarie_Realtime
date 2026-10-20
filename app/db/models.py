import uuid
from datetime import datetime
from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    room_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    create_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)