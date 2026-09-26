"""Add meeting_indexes table.

Revision ID: e1f4a9b2c3d5
Revises: 9d4e5f61a2b3
"""
from typing import Sequence, Union

# pyrefly: ignore [missing-import]
from alembic import op
# pyrefly: ignore [missing-import]
import sqlalchemy as sa


revision: str = "e1f4a9b2c3d5"
down_revision: Union[str, Sequence[str], None] = "9d4e5f61a2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "meeting_indexes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("meeting_id", sa.String(), nullable=False),
        sa.Column("chunks_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("collection_name", sa.String(), nullable=False),
        sa.Column("embedding_model", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id"),
    )
    op.create_index("ix_meeting_indexes_meeting_id", "meeting_indexes", ["meeting_id"])


def downgrade() -> None:
    op.drop_index("ix_meeting_indexes_meeting_id", table_name="meeting_indexes")
    op.drop_table("meeting_indexes")
