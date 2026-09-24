from datetime import datetime, timezone
import json
from unittest.mock import patch

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
from app.models import Meeting, MeetingIntelligence, Transcript


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
    db.query(MeetingIntelligence).delete()
    db.query(Transcript).delete()
    db.query(Meeting).delete()
    db.commit()
    db.close()


def test_start_intelligence_success():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-intel-ready",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="done",
            file_path="meeting.wav",
        )
    )
    db.add(
        Transcript(
            id="trans-1",
            meeting_id="meeting-intel-ready",
            transcript_path="transcripts/dummy.json",
            segments_json='[{"speaker": "Speaker 1", "text": "Hello"}]',
            whisper_model="small",
            diarization_model="pyannote/speaker-diarization-3.1",
        )
    )
    db.commit()
    db.close()

    with patch("app.routers.meetings.process_meeting_intelligence") as mock_worker:
        response = client.post("/meetings/meeting-intel-ready/intelligence")
        assert response.status_code == 202
        assert response.json() == {"meeting_id": "meeting-intel-ready", "status": "processing"}
        mock_worker.assert_called_once_with("meeting-intel-ready")


def test_start_intelligence_rerun_on_already_analyzed():
    """Verify that re-running intelligence on an analyzed meeting is allowed."""
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-already-analyzed",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="analyzed",
            file_path="meeting.wav",
        )
    )
    db.add(
        Transcript(
            id="trans-2",
            meeting_id="meeting-already-analyzed",
            transcript_path="transcripts/dummy.json",
            segments_json='[{"speaker": "Speaker 1", "text": "Hello again"}]',
            whisper_model="small",
            diarization_model="pyannote/speaker-diarization-3.1",
        )
    )
    db.commit()
    db.close()

    with patch("app.routers.meetings.process_meeting_intelligence") as mock_worker:
        response = client.post("/meetings/meeting-already-analyzed/intelligence")
        assert response.status_code == 202
        assert response.json() == {"meeting_id": "meeting-already-analyzed", "status": "processing"}
        mock_worker.assert_called_once_with("meeting-already-analyzed")


def test_start_intelligence_retry_on_failed():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-previously-failed",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="failed",
            file_path="meeting.wav",
        )
    )
    db.add(
        Transcript(
            id="trans-3",
            meeting_id="meeting-previously-failed",
            transcript_path="transcripts/dummy.json",
            segments_json='[{"speaker": "Speaker 1", "text": "Hello"}]',
            whisper_model="small",
            diarization_model="pyannote/speaker-diarization-3.1",
        )
    )
    db.commit()
    db.close()

    with patch("app.routers.meetings.process_meeting_intelligence") as mock_worker:
        response = client.post("/meetings/meeting-previously-failed/intelligence")
        assert response.status_code == 202
        mock_worker.assert_called_once_with("meeting-previously-failed")


def test_start_intelligence_meeting_not_found():
    response = client.post("/meetings/non-existent/intelligence")
    assert response.status_code == 404
    assert response.json()["detail"] == "Meeting not found"


def test_start_intelligence_already_processing():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-proc",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="processing",
            file_path="meeting.wav",
        )
    )
    db.commit()
    db.close()

    response = client.post("/meetings/meeting-proc/intelligence")
    assert response.status_code == 400
    assert "current status: processing" in response.json()["detail"]


def test_start_intelligence_uploaded_not_ready():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-uploaded",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="uploaded",
            file_path="meeting.wav",
        )
    )
    db.commit()
    db.close()

    response = client.post("/meetings/meeting-uploaded/intelligence")
    assert response.status_code == 400
    assert "current status: uploaded" in response.json()["detail"]


def test_start_intelligence_missing_transcript():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-no-transcript",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="done",
            file_path="meeting.wav",
        )
    )
    db.commit()
    db.close()

    response = client.post("/meetings/meeting-no-transcript/intelligence")
    assert response.status_code == 400
    assert "Transcript not found" in response.json()["detail"]


def test_get_intelligence_processing():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-proc-get",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="processing",
            file_path="meeting.wav",
        )
    )
    db.commit()
    db.close()

    response = client.get("/meetings/meeting-proc-get/intelligence")
    assert response.status_code == 200
    assert response.json() == {"meeting_id": "meeting-proc-get", "status": "processing"}


def test_get_intelligence_failed():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-fail-get",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="failed",
            file_path="meeting.wav",
        )
    )
    db.commit()
    db.close()

    response = client.get("/meetings/meeting-fail-get/intelligence")
    assert response.status_code == 500
    assert response.json()["detail"] == "Processing failed"


def test_get_intelligence_meeting_not_found():
    response = client.get("/meetings/non-existent/intelligence")
    assert response.status_code == 404
    assert response.json()["detail"] == "Meeting not found"


def test_get_intelligence_result_not_found():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-done-no-intel",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="done",
            file_path="meeting.wav",
        )
    )
    db.commit()
    db.close()

    response = client.get("/meetings/meeting-done-no-intel/intelligence")
    assert response.status_code == 404
    assert response.json()["detail"] == "Intelligence result not found"


def test_get_intelligence_success():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-analyzed-get",
            filename="meeting.wav",
            upload_time=datetime.now(timezone.utc),
            status="analyzed",
            file_path="meeting.wav",
        )
    )
    db.add(
        MeetingIntelligence(
            id="intel-rec-1",
            meeting_id="meeting-analyzed-get",
            summary="Executive summary of discussion.",
            key_points_json=json.dumps(["Topic 1", "Topic 2"]),
            decisions_json=json.dumps(["Decision 1"]),
            action_items_json=json.dumps([
                {"task": "Task 1", "assignee": "Alice", "deadline": "Friday"},
                {"task": "Task 2", "assignee": None, "deadline": None},
            ]),
            intelligence_path="data/intelligence/meeting-analyzed-get.json",
            model_name="gemini-2.5-flash",
        )
    )
    db.commit()
    db.close()

    response = client.get("/meetings/meeting-analyzed-get/intelligence")
    assert response.status_code == 200
    data = response.json()
    assert data["meeting_id"] == "meeting-analyzed-get"
    assert data["status"] == "analyzed"
    assert data["summary"] == "Executive summary of discussion."
    assert data["key_points"] == ["Topic 1", "Topic 2"]
    assert data["decisions"] == ["Decision 1"]
    assert len(data["action_items"]) == 2
    assert data["action_items"][0] == {"task": "Task 1", "assignee": "Alice", "deadline": "Friday"}
    assert data["action_items"][1] == {"task": "Task 2", "assignee": None, "deadline": None}


def test_list_meetings_and_get_meeting():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-list-1",
            filename="weekly_sync.mp3",
            upload_time=datetime.now(timezone.utc),
            status="analyzed",
            file_path="uploads/weekly_sync.mp3",
        )
    )
    db.add(
        Transcript(
            id="trans-list-1",
            meeting_id="meeting-list-1",
            transcript_path="transcripts/dummy.json",
            segments_json="[]",
            whisper_model="small",
            diarization_model="pyannote/speaker-diarization-3.1",
        )
    )
    db.add(
        MeetingIntelligence(
            id="intel-list-1",
            meeting_id="meeting-list-1",
            summary="Sync summary",
            key_points_json="[]",
            decisions_json="[]",
            action_items_json="[]",
            intelligence_path="data/intelligence/meeting-list-1.json",
            model_name="gemini-2.5-flash",
        )
    )
    db.commit()
    db.close()

    # Test list endpoint
    res = client.get("/meetings")
    assert res.status_code == 200
    meetings = res.json()
    assert len(meetings) == 1
    assert meetings[0]["id"] == "meeting-list-1"
    assert meetings[0]["has_transcript"] is True
    assert meetings[0]["has_intelligence"] is True
    assert meetings[0]["status"] == "analyzed"

    # Test detail endpoint
    res_detail = client.get("/meetings/meeting-list-1")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["id"] == "meeting-list-1"
    assert detail["filename"] == "weekly_sync.mp3"
    assert detail["has_transcript"] is True
    assert detail["has_intelligence"] is True

    # Test 404 for unknown meeting
    res_404 = client.get("/meetings/unknown-meeting-uuid")
    assert res_404.status_code == 404

