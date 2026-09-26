import json
from unittest.mock import patch

# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker
# pyrefly: ignore [missing-import]
from sqlalchemy.pool import StaticPool

# pyrefly: ignore [missing-import]
from app.database import Base
from app.models import Meeting, MeetingIndex, MeetingIntelligence, Transcript
from app.services.indexing_processing import process_meeting_indexing


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


@patch("app.services.indexing_processing.SessionLocal")
@patch("app.services.indexing_processing.embed_batch")
@patch("app.services.indexing_processing.insert_chunks")
@patch("app.services.indexing_processing.delete_meeting_points")
@patch("app.services.indexing_processing.ensure_collection")
def test_process_meeting_indexing_success(
    mock_ensure,
    mock_delete,
    mock_insert,
    mock_embed,
    mock_session_local,
):
    db = TestingSessionLocal()
    mock_session_local.return_value = db

    meeting = Meeting(id="m-index-test", filename="test.mp3", status="analyzed", file_path="dummy.mp3")
    transcript = Transcript(
        meeting_id="m-index-test",
        transcript_path="dummy.json",
        segments_json=json.dumps([{"speaker": "Speaker 1", "start": 0, "end": 2, "text": "Testing index"}]),
        whisper_model="small",
        diarization_model="pyannote",
    )
    intel = MeetingIntelligence(
        meeting_id="m-index-test",
        summary="A test summary",
        key_points_json=json.dumps(["Point 1"]),
        decisions_json=json.dumps(["Decision 1"]),
        action_items_json=json.dumps([{"task": "Task 1", "assignee": "Alice", "deadline": "soon"}]),
        intelligence_path="dummy.json",
        model_name="gemini",
    )
    db.add(meeting)
    db.add(transcript)
    db.add(intel)
    db.commit()

    mock_embed.return_value = [[0.1] * 384] * 4
    mock_insert.return_value = 4

    process_meeting_indexing("m-index-test")

    updated_meeting = db.get(Meeting, "m-index-test")
    assert updated_meeting.status == "indexed"
    assert updated_meeting.processing_error is None

    idx_record = db.query(MeetingIndex).filter(MeetingIndex.meeting_id == "m-index-test").first()
    assert idx_record is not None
    assert idx_record.chunks_count == 4
    db.close()


@patch("app.services.indexing_processing.SessionLocal")
def test_process_meeting_indexing_missing_transcript(mock_session_local):
    db = TestingSessionLocal()
    mock_session_local.return_value = db

    meeting = Meeting(id="m-no-transcript", filename="test.mp3", status="analyzed", file_path="dummy.mp3")
    db.add(meeting)
    db.commit()

    process_meeting_indexing("m-no-transcript")

    updated = db.get(Meeting, "m-no-transcript")
    assert updated.status == "failed"
    assert updated.processing_error == "ValueError"
    db.close()
