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
