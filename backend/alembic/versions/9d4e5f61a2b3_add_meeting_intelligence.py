"""Add meeting_intelligence table.

Revision ID: 9d4e5f61a2b3
Revises: 7c1c2f90f8c7
"""
from typing import Sequence, Union

# pyrefly: ignore [missing-import]
from alembic import op
# pyrefly: ignore [missing-import]
import sqlalchemy as sa


revision: str = "9d4e5f61a2b3"
down_revision: Union[str, Sequence[str], None] = "7c1c2f90f8c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "meeting_intelligence",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("meeting_id", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("key_points_json", sa.Text(), nullable=False),
        sa.Column("decisions_json", sa.Text(), nullable=False),
        sa.Column("action_items_json", sa.Text(), nullable=False),
        sa.Column("intelligence_path", sa.String(), nullable=False),
        sa.Column("model_name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id"),
    )
    op.create_index("ix_meeting_intelligence_meeting_id", "meeting_intelligence", ["meeting_id"])


def downgrade() -> None:
    op.drop_index("ix_meeting_intelligence_meeting_id", table_name="meeting_intelligence")
    op.drop_table("meeting_intelligence")
