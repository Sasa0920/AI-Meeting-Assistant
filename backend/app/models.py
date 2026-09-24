# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, DateTime, Text
from app.database import Base
import uuid
from datetime import datetime, timezone

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    upload_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, nullable=False, default="uploaded")
    file_path = Column(String, nullable=False)
    processing_error = Column(String, nullable=True)


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, nullable=False, unique=True, index=True)
    transcript_path = Column(String, nullable=False)
    segments_json = Column(Text, nullable=False)
    whisper_model = Column(String, nullable=False)
    diarization_model = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class MeetingIntelligence(Base):
    __tablename__ = "meeting_intelligence"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, nullable=False, unique=True, index=True)
    summary = Column(Text, nullable=False)
    key_points_json = Column(Text, nullable=False)
    decisions_json = Column(Text, nullable=False)
    action_items_json = Column(Text, nullable=False)
    intelligence_path = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

