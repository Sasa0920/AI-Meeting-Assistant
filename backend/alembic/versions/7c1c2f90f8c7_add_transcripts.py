"""Add transcript storage and processing error.

Revision ID: 7c1c2f90f8c7
Revises: b4b84891332e
"""
from typing import Sequence, Union

# pyrefly: ignore [missing-import]
from alembic import op
# pyrefly: ignore [missing-import]
import sqlalchemy as sa


revision: str = "7c1c2f90f8c7"
down_revision: Union[str, Sequence[str], None] = "b4b84891332e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("meetings", sa.Column("processing_error", sa.String(), nullable=True))
    op.create_table(
        "transcripts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("meeting_id", sa.String(), nullable=False),
        sa.Column("transcript_path", sa.String(), nullable=False),
        sa.Column("segments_json", sa.Text(), nullable=False),
        sa.Column("whisper_model", sa.String(), nullable=False),
        sa.Column("diarization_model", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id"),
    )
    op.create_index("ix_transcripts_meeting_id", "transcripts", ["meeting_id"])


def downgrade() -> None:
    op.drop_index("ix_transcripts_meeting_id", table_name="transcripts")
    op.drop_table("transcripts")
    op.drop_column("meetings", "processing_error")
