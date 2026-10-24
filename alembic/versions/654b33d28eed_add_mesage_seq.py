"""add message seq

Revision ID: 654b33d28eed
Revises: 800c00277c5c
Create Date: 2026-10-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '654b33d28eed'
down_revision: Union[str, Sequence[str], None] = '800c00277c5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("messages", sa.Column("seq", sa.BigInteger(), sa.Identity(), nullable=False))
    op.create_index("ix_messages_room_seq", "messages", ["room_id", "seq"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_messages_room_seq", table_name="messages")
    op.drop_column("messages", "seq")