from datetime import datetime, timezone

# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker
# pyrefly: ignore [missing-import]
from sqlalchemy.pool import StaticPool

# pyrefly: ignore [missing-import]
from app.database import Base, get_db
# pyrefly: ignore [missing-import]
from app.main import app
# pyrefly: ignore [missing-import]
from app.models import Meeting, Transcript


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()
    db.query(Transcript).delete()
    db.query(Meeting).delete()
    db.commit()
    db.close()


def test_transcript_returns_processing_status():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="processing-meeting",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="processing",
            file_path="meeting.wav",
        )
    )
    db.commit()
    db.close()

    response = client.get("/meetings/processing-meeting/transcript")

    assert response.status_code == 200
    assert response.json() == {"meeting_id": "processing-meeting", "status": "processing"}


def test_transcript_returns_saved_segments():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="done-meeting",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="done",
            file_path="meeting.wav",
        )
    )
    db.add(
        Transcript(
            id="transcript-1",
            meeting_id="done-meeting",
            transcript_path="transcripts/done-meeting.json",
            segments_json='[{"speaker":"Speaker 1","start":0.0,"end":1.2,"text":"Hello"}]',
            whisper_model="small",
            diarization_model="pyannote/speaker-diarization-3.1",
        )
    )
    db.commit()
    db.close()

    response = client.get("/meetings/done-meeting/transcript")

    assert response.status_code == 200
    assert response.json()["transcript"] == [
        {"speaker": "Speaker 1", "start": 0.0, "end": 1.2, "text": "Hello"}
    ]


def test_process_meeting_triggers_processing(tmp_path):
    from unittest.mock import patch

    fake_audio = tmp_path / "meeting.wav"
    fake_audio.write_bytes(b"dummy audio content")

    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="to-process",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="uploaded",
            file_path=str(fake_audio),
        )
    )
    db.commit()
    db.close()

    with patch("app.routers.meetings.process_meeting") as mock_process:
        response = client.post("/meetings/to-process/process")
        assert response.status_code == 202
        assert response.json() == {"meeting_id": "to-process", "status": "processing"}
        mock_process.assert_called_once_with("to-process")


def test_process_meeting_not_found():
    response = client.post("/meetings/non-existent/process")
    assert response.status_code == 404


def test_process_meeting_already_processed():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="already-done",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="done",
            file_path="meeting.wav",
        )
    )
    db.commit()
    db.close()

    response = client.post("/meetings/already-done/process")
    assert response.status_code == 400


def test_process_meeting_file_not_found():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="missing-file",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="uploaded",
            file_path="non_existent_file.wav",
        )
    )
    db.commit()
    db.close()

    response = client.post("/meetings/missing-file/process")
    assert response.status_code == 400


def test_transcript_meeting_not_found():
    response = client.get("/meetings/non-existent/transcript")
    assert response.status_code == 404


def test_transcript_meeting_failed():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="failed-meeting",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="failed",
            file_path="meeting.wav",
            processing_error="OSError",
        )
    )
    db.commit()
    db.close()

    response = client.get("/meetings/failed-meeting/transcript")
    assert response.status_code == 500
    assert response.json()["detail"] == "Processing failed"


def test_transcript_persists_when_indexed_and_during_indexing():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-idx-trans",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="indexed",
            file_path="meeting.wav",
        )
    )
    db.add(
        Transcript(
            id="trans-idx-1",
            meeting_id="meeting-idx-trans",
            transcript_path="transcripts/dummy.json",
            segments_json='[{"speaker":"Speaker 1","start":0.0,"end":1.0,"text":"Retained"}]',
            whisper_model="small",
            diarization_model="pyannote/speaker-diarization-3.1",
        )
    )
    db.commit()
    db.close()

    # When indexed
    res = client.get("/meetings/meeting-idx-trans/transcript")
    assert res.status_code == 200
    assert len(res.json()["transcript"]) == 1
    assert res.json()["transcript"][0]["text"] == "Retained"

    # When status is temporarily processing (e.g. re-indexing)
    db = TestingSessionLocal()
    m = db.get(Meeting, "meeting-idx-trans")
    m.status = "processing"
    db.commit()
    db.close()

    res2 = client.get("/meetings/meeting-idx-trans/transcript")
    assert res2.status_code == 200
    assert len(res2.json()["transcript"]) == 1
    assert res2.json()["transcript"][0]["text"] == "Retained"
