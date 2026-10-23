from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import RoomMember

def is_room_member(room_id: str, user_id: str) -> bool:

    with SessionLocal() as session:
        statement = select(RoomMember).where(RoomMember.room_id == room_id, RoomMember.user_id == user_id)

        return session.scalar(statement) is not None
    

    