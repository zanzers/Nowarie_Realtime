"""add client message id

Revision ID: 7f0cdbc880b8
Revises: 654b33d28eed
Create Date: 2026-10-24 23:44:50.431956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f0cdbc880b8'
down_revision: Union[str, Sequence[str], None] = '654b33d28eed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("client_message_id", sa.String(64), nullable=True))
    op.create_unique_constraint(
        "uq_messages_room_sender_client_message_id",
        "messages",
        ["room_id", "sender", "client_message_id"],
    )

def downgrade() -> None:
    op.drop_constraint("uq_messages_room_sender_client_message_id", "messages", type_="unique")
    op.drop_column("messages", "client_message_id")