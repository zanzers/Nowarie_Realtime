import uuid
from datetime import datetime
from sqlalchemy import DateTime, String, Text, BigInteger, Identity, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base

class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("room_id", "sender", "client_message_id", name="uq_message_room_sender_client_message_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    room_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    seq: Mapped[int] = mapped_column(BigInteger, Identity(), nullable=False)
    client_message_id: Mapped[str | None] = mapped_column(String(64), nullable=True)



class RoomMember(Base):
    __tablename__ = "room_members"

    room_id: Mapped[str] = mapped_column( String(100), primary_key=True)
    user_id: Mapped[str] = mapped_column( String(100), primary_key=True)