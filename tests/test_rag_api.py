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
from app.models import Meeting, MeetingIndex, MeetingIntelligence, Transcript
from app.schemas import RAGQueryResponse, RAGSourceChunk


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
    db.query(MeetingIndex).delete()
    db.query(MeetingIntelligence).delete()
    db.query(Transcript).delete()
    db.query(Meeting).delete()
    db.commit()
    db.close()


def test_index_meeting_not_found():
    response = client.post("/meetings/unknown-id/index")
    assert response.status_code == 404
    assert response.json()["detail"] == "Meeting not found"


def test_index_meeting_not_ready():
    db = TestingSessionLocal()
    meeting = Meeting(id="m-uploaded", filename="test.mp3", status="uploaded", file_path="dummy.mp3")
    db.add(meeting)
    db.commit()
    db.close()

    response = client.post("/meetings/m-uploaded/index")
    assert response.status_code == 400
    assert "Meeting is not ready" in response.json()["detail"]


def test_index_meeting_no_transcript():
    db = TestingSessionLocal()
    meeting = Meeting(id="m-analyzed", filename="test.mp3", status="analyzed", file_path="dummy.mp3")
    db.add(meeting)
    db.commit()
    db.close()

    response = client.post("/meetings/m-analyzed/index")
    assert response.status_code == 400
    assert "Transcript not found" in response.json()["detail"]


@patch("app.routers.meetings.process_meeting_indexing")
def test_index_meeting_success_202(mock_indexing_task):
    db = TestingSessionLocal()
    meeting = Meeting(id="m-ready", filename="test.mp3", status="analyzed", file_path="dummy.mp3")
    transcript = Transcript(
        meeting_id="m-ready",
        transcript_path="dummy.json",
        segments_json=json.dumps([{"speaker": "Speaker 1", "start": 0, "end": 1, "text": "hello"}]),
        whisper_model="small",
        diarization_model="pyannote",
    )
    db.add(meeting)
    db.add(transcript)
    db.commit()
    db.close()

    response = client.post("/meetings/m-ready/index")
    assert response.status_code == 202
    assert response.json() == {"meeting_id": "m-ready", "status": "processing"}

    db = TestingSessionLocal()
    updated = db.get(Meeting, "m-ready")
    assert updated.status == "processing"
    db.close()


def test_meeting_detail_includes_has_index():
    db = TestingSessionLocal()
    meeting = Meeting(id="m-detail", filename="test.mp3", status="indexed", file_path="dummy.mp3")
    idx = MeetingIndex(
        meeting_id="m-detail",
        chunks_count=5,
        collection_name="meeting_knowledge",
        embedding_model="all-MiniLM-L6-v2",
    )
    db.add(meeting)
    db.add(idx)
    db.commit()
    db.close()

    response = client.get("/meetings/m-detail")
    assert response.status_code == 200
    data = response.json()
    assert data["has_index"] is True


def test_meeting_list_includes_has_index():
    db = TestingSessionLocal()
    meeting = Meeting(id="m-list", filename="test.mp3", status="indexed", file_path="dummy.mp3")
    idx = MeetingIndex(
        meeting_id="m-list",
        chunks_count=3,
        collection_name="meeting_knowledge",
        embedding_model="all-MiniLM-L6-v2",
    )
    db.add(meeting)
    db.add(idx)
    db.commit()
    db.close()

    response = client.get("/meetings")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["has_index"] is True


@patch("app.routers.rag.answer_meeting_query")
def test_rag_query_endpoint(mock_answer):
    mock_answer.return_value = RAGQueryResponse(
        query="What is the plan?",
        answer="The plan is to launch next month.",
        sources=[
            RAGSourceChunk(
                meeting_id="m-1",
                filename="sprint.mp3",
                speaker="Speaker 1",
                start_time=1.0,
                end_time=5.0,
                text="We launch next month.",
                score=0.92,
            )
        ],
        insufficient_evidence=False,
    )

    response = client.post("/rag/query", json={"query": "What is the plan?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "The plan is to launch next month."
    assert len(data["sources"]) == 1
    assert data["insufficient_evidence"] is False


@patch("app.routers.rag.semantic_search_chunks")
def test_rag_search_endpoint(mock_search):
    mock_search.return_value = [
        RAGSourceChunk(
            meeting_id="m-1",
            filename="sprint.mp3",
            speaker="Speaker 1",
            start_time=0.0,
            end_time=3.0,
            text="Redis caching discussion",
            score=0.85,
        )
    ]

    response = client.post("/rag/search", json={"query": "Redis caching"})
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Redis caching"
    assert len(data["results"]) == 1
    assert data["results"][0]["meeting_id"] == "m-1"
