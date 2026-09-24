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
from app.models import Meeting, MeetingIntelligence, Transcript
# pyrefly: ignore [missing-import]
from app.schemas import ActionItem, MeetingIntelligenceOutput
# pyrefly: ignore [missing-import]
from app.services.intelligence_processing import process_meeting_intelligence


def test_process_meeting_intelligence_success(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr("app.services.intelligence_processing.SessionLocal", TestingSession)
    intelligence_dir = str(tmp_path / "intelligence")
    monkeypatch.setattr("app.services.intelligence_processing.settings.INTELLIGENCE_DIR", intelligence_dir)

    db = TestingSession()
    meeting = Meeting(
        id="meeting-intel-1",
        filename="audio.wav",
        upload_time=datetime.now(timezone.utc),
        status="processing",
        file_path="audio.wav",
    )
    segments = [
        {"speaker": "Speaker 1", "start": 0.0, "end": 4.0, "text": "Let's optimize the queries today."},
        {"speaker": "Speaker 2", "start": 4.1, "end": 8.0, "text": "I will add the index by Thursday."},
    ]
    transcript = Transcript(
        id="transcript-intel-1",
        meeting_id="meeting-intel-1",
        transcript_path="transcripts/dummy.json",
        segments_json=json.dumps(segments),
        whisper_model="small",
        diarization_model="pyannote/speaker-diarization-3.1",
    )
    db.add(meeting)
    db.add(transcript)
    db.commit()
    db.close()

    mock_output = MeetingIntelligenceOutput(
        summary="Team discussed slow database queries and agreed to add an index.",
        key_points=["Database query optimization", "Index addition"],
        decisions=["Optimize queries rather than adding caching"],
        action_items=[
            ActionItem(task="Add index to meeting_id column", assignee="Speaker 2", deadline="Thursday")
        ],
    )

    with patch("app.services.intelligence_processing.extract_meeting_intelligence", return_value=mock_output):
        process_meeting_intelligence("meeting-intel-1")

    db = TestingSession()
    m = db.get(Meeting, "meeting-intel-1")
    assert m.status == "analyzed"
    assert m.processing_error is None

    intel_record = db.query(MeetingIntelligence).filter(MeetingIntelligence.meeting_id == "meeting-intel-1").first()
    assert intel_record is not None
    assert intel_record.summary == mock_output.summary
    assert json.loads(intel_record.key_points_json) == ["Database query optimization", "Index addition"]
    assert json.loads(intel_record.decisions_json) == ["Optimize queries rather than adding caching"]
    
    action_items_db = json.loads(intel_record.action_items_json)
    assert len(action_items_db) == 1
    assert action_items_db[0]["task"] == "Add index to meeting_id column"
    assert action_items_db[0]["assignee"] == "Speaker 2"
    assert action_items_db[0]["deadline"] == "Thursday"

    assert os.path.exists(intel_record.intelligence_path)
    with open(intel_record.intelligence_path, "r", encoding="utf-8") as f:
        file_content = json.load(f)
    assert file_content["meeting_id"] == "meeting-intel-1"
    assert file_content["status"] == "analyzed"
    assert file_content["summary"] == mock_output.summary
    db.close()


def test_process_meeting_intelligence_rerun_success(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr("app.services.intelligence_processing.SessionLocal", TestingSession)
    intelligence_dir = str(tmp_path / "intelligence")
    monkeypatch.setattr("app.services.intelligence_processing.settings.INTELLIGENCE_DIR", intelligence_dir)

    db = TestingSession()
    meeting = Meeting(
        id="meeting-rerun",
        filename="audio.wav",
        upload_time=datetime.now(timezone.utc),
        status="processing",
        file_path="audio.wav",
    )
    transcript = Transcript(
        id="transcript-rerun",
        meeting_id="meeting-rerun",
        transcript_path="transcripts/dummy.json",
        segments_json='[{"speaker":"Speaker 1","text":"Old discussion"}]',
        whisper_model="small",
        diarization_model="pyannote/speaker-diarization-3.1",
    )
    old_intel = MeetingIntelligence(
        id="old-intel-id",
        meeting_id="meeting-rerun",
        summary="Old summary",
        key_points_json="[]",
        decisions_json="[]",
        action_items_json="[]",
        intelligence_path="old/path.json",
        model_name="gemini-2.5-flash",
    )
    db.add(meeting)
    db.add(transcript)
    db.add(old_intel)
    db.commit()
    db.close()

    new_output = MeetingIntelligenceOutput(
        summary="Updated fresh summary",
        key_points=["Fresh topic"],
        decisions=["Fresh decision"],
        action_items=[],
    )

    with patch("app.services.intelligence_processing.extract_meeting_intelligence", return_value=new_output):
        process_meeting_intelligence("meeting-rerun")

    db = TestingSession()
    m = db.get(Meeting, "meeting-rerun")
    assert m.status == "analyzed"
    all_intel = db.query(MeetingIntelligence).filter(MeetingIntelligence.meeting_id == "meeting-rerun").all()
    assert len(all_intel) == 1
    assert all_intel[0].summary == "Updated fresh summary"
    db.close()


def test_process_meeting_intelligence_missing_transcript(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr("app.services.intelligence_processing.SessionLocal", TestingSession)

    db = TestingSession()
    meeting = Meeting(
        id="meeting-no-trans",
        filename="audio.wav",
        upload_time=datetime.now(timezone.utc),
        status="processing",
        file_path="audio.wav",
    )
    db.add(meeting)
    db.commit()
    db.close()

    process_meeting_intelligence("meeting-no-trans")

    db = TestingSession()
    m = db.get(Meeting, "meeting-no-trans")
    assert m.status == "failed"
    assert m.processing_error == "ValueError"
    db.close()


def test_process_meeting_intelligence_failure_cleans_up(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr("app.services.intelligence_processing.SessionLocal", TestingSession)
    intelligence_dir = str(tmp_path / "intelligence")
    monkeypatch.setattr("app.services.intelligence_processing.settings.INTELLIGENCE_DIR", intelligence_dir)

    db = TestingSession()
    meeting = Meeting(
        id="meeting-fail",
        filename="audio.wav",
        upload_time=datetime.now(timezone.utc),
        status="processing",
        file_path="audio.wav",
    )
    transcript = Transcript(
        id="transcript-fail",
        meeting_id="meeting-fail",
        transcript_path="transcripts/dummy.json",
        segments_json='[{"speaker":"Speaker 1","text":"Hi"}]',
        whisper_model="small",
        diarization_model="pyannote/speaker-diarization-3.1",
    )
    db.add(meeting)
    db.add(transcript)
    db.commit()
    db.close()

    with patch("app.services.intelligence_processing.extract_meeting_intelligence", side_effect=RuntimeError("API Quota exceeded")):
        process_meeting_intelligence("meeting-fail")

    db = TestingSession()
    m = db.get(Meeting, "meeting-fail")
    assert m.status == "failed"
    assert m.processing_error == "RuntimeError"

    # Verify no dangling file in intelligence_dir
    expected_file = os.path.join(intelligence_dir, "meeting-fail.json")
    assert not os.path.exists(expected_file)
    db.close()
