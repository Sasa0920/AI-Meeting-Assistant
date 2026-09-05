import json
import os
from datetime import datetime, timezone
from unittest.mock import patch

# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker
# pyrefly: ignore [missing-import]
from sqlalchemy.pool import StaticPool

# pyrefly: ignore [missing-import]
from app.database import Base
# pyrefly: ignore [missing-import]
from app.models import Meeting, Transcript
# pyrefly: ignore [missing-import]
from app.services.processing import process_meeting


def test_process_meeting_success(tmp_path, monkeypatch):
    # Set up isolated in-memory DB
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr("app.services.processing.SessionLocal", TestingSession)
    transcript_dir = str(tmp_path / "transcripts")
    monkeypatch.setattr("app.services.processing.settings.TRANSCRIPT_DIR", transcript_dir)

    fake_audio = tmp_path / "audio.wav"
    fake_audio.write_bytes(b"dummy audio")

    db = TestingSession()
    meeting = Meeting(
        id="test-pipe-1",
        filename="audio.wav",
        upload_time=datetime.now(timezone.utc),
        status="processing",
        file_path=str(fake_audio),
    )
    db.add(meeting)
    db.commit()
    db.close()

    mock_transcription = [
        {"start": 0.0, "end": 2.0, "text": "Hello team", "words": [{"start": 0.0, "end": 2.0, "word": "Hello team"}]}
    ]
    mock_diarization = [{"start": 0.0, "end": 2.0, "speaker": "SPEAKER_00"}]

    with (
        patch("app.services.processing.transcribe_audio", return_value=mock_transcription),
        patch("app.services.processing.diarize_audio", return_value=mock_diarization),
    ):
        process_meeting("test-pipe-1")

    db = TestingSession()
    m = db.get(Meeting, "test-pipe-1")
    assert m.status == "done"
    assert m.processing_error is None

    transcript_record = db.query(Transcript).filter(Transcript.meeting_id == "test-pipe-1").first()
    assert transcript_record is not None
    segments = json.loads(transcript_record.segments_json)
    assert len(segments) == 1
    assert segments[0]["speaker"] == "Speaker 1"
    assert segments[0]["text"] == "Hello team"

    assert os.path.exists(transcript_record.transcript_path)
    db.close()


def test_process_meeting_handles_pipeline_failure(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr("app.services.processing.SessionLocal", TestingSession)
    transcript_dir = str(tmp_path / "transcripts")
    monkeypatch.setattr("app.services.processing.settings.TRANSCRIPT_DIR", transcript_dir)

    fake_audio = tmp_path / "audio.wav"
    fake_audio.write_bytes(b"dummy audio")

    db = TestingSession()
    meeting = Meeting(
        id="test-pipe-fail",
        filename="audio.wav",
        upload_time=datetime.now(timezone.utc),
        status="processing",
        file_path=str(fake_audio),
    )
    db.add(meeting)
    db.commit()
    db.close()

    with patch("app.services.processing.transcribe_audio", side_effect=OSError("Test error")):
        process_meeting("test-pipe-fail")

    db = TestingSession()
    m = db.get(Meeting, "test-pipe-fail")
    assert m.status == "failed"
    assert m.processing_error == "OSError"
    db.close()
