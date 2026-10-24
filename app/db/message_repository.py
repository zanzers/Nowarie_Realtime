import uuid
from sqlalchemy import select, desc
from app.db.database import SessionLocal
from app.db.models import Message
from app.db.schemas.schemas import MessageEvent

class UnknownMessageError(Exception):
    pass

def _to_event(message: Message) -> MessageEvent:
    return MessageEvent(
        type="chat.message",
        id=message.id.hex,
        sender=message.sender,
        content=message.content,
        timestamp=message.created_at
    )

def save_message(message: MessageEvent, room_id: str) -> None:
    message_id = uuid.UUID(hex=message.id)

    with SessionLocal() as session:
        existing_message = session.scalar(
            select(Message).where(Message.id == message_id)
        )

        if existing_message is not None:
            if( existing_message.room_id != room_id or existing_message.sender != message.sender or existing_message.content != message.content or existing_message.created_at != message.timestamp):

                raise ValueError("Message ID already exists with different content.")
            
            return
        
        db_message =  Message(
            id=message_id,
            room_id=room_id,
            sender=message.sender,
            content=message.content,
            created_at=message.timestamp
        )

        session.add(db_message)
        session.commit()


def get_messages(room_id: str, limit: int = 50) -> list[MessageEvent]:
    with SessionLocal() as session:
        statement = (
            select(Message)
            .where(Message.room_id == room_id)
            .order_by(desc(Message.created_at), desc(Message.id))
            .limit(limit)
        )
        
        messages = session.scalars(statement).all()

        return [
            MessageEvent(
                type="chat.message",
                id=message.id.hex,
                sender=message.sender,
                content=message.content,
                timestamp=message.created_at,
            )
            for message in reversed(messages)
        ]

def get_messages_after(room_id: str, after_id: str, limit: int = 100) -> list[MessageEvent]:
    with SessionLocal() as session:
        anchor_seq = session.scalar(
            select(Message.seq).where(
                Message.id == uuid.UUID(hex=after_id),
                Message.room_id == room_id,
            )
        )

        if anchor_seq is None:
            raise UnknownMessageError(after_id)

        statement = (
            select(Message)
            .where(Message.room_id == room_id, Message.seq > anchor_seq)
            .order_by(Message.seq.asc())
            .limit(limit)
        )

        return [_to_event(m) for m in session.scalars(statement).all()]

