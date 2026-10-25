import uuid
from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError
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
        timestamp=message.created_at,
        client_message_id=message.client_message_id
    )

def _find_by_client_id(session, room_id: str, sender: str, client_message_id: str):
    return session.scalar(
        select(Message).where(
            Message.room_id == room_id,
            Message.sender == sender,
            Message.client_message_id == client_message_id,
        )
    )
   

def save_message(message: MessageEvent, room_id: str) -> MessageEvent:
    message_id = uuid.UUID(hex=message.id)

    with SessionLocal() as session:
        existing_message = session.scalar( select(Message).where(Message.id == message_id))

        if existing_message is not None:
            if( existing_message.room_id != room_id or existing_message.sender != message.sender or existing_message.content != message.content or existing_message.created_at != message.timestamp or existing_message.client_message_id != message.client_message_id):

                raise ValueError("Message ID already exists with different content.")
            
            return _to_event(existing_message)

        if message.client_message_id is not None:
            duplicate = _find_by_client_id(session, room_id, message.sender, message.client_message_id)
            if duplicate is not None:
                return _to_event(duplicate)
        
        session.add(Message(
            id=message_id,
            room_id=room_id,
            sender=message.sender,
            content=message.content,
            created_at=message.timestamp,
            client_message_id=message.client_message_id
        ))

        try:
            session.commit()
        
        except IntegrityError:
            session.rollback()

            if message.client_message_id is None:
                raise
            duplicate = _find_by_client_id(session, room_id, message.sender, message.client_message_id)
            
            if duplicate is None:
                raise
            return _to_event(duplicate)

        return message


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

