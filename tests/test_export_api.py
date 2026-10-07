import io
import json
from datetime import datetime, timezone

# pyrefly: ignore [missing-import]
from docx import Document
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker
# pyrefly: ignore [missing-import]
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
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


def test_export_meeting_not_found():
    response = client.get("/meetings/non-existent-meeting/export?format=pdf")
    assert response.status_code == 404
    assert response.json()["error"] == "Meeting not found"


def test_export_meeting_not_ready():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-not-ready",
            filename="standup.mp3",
            upload_time=datetime(2026, 8, 31, 10, 0, 0, tzinfo=timezone.utc),
            status="processing",
            file_path="standup.mp3",
        )
    )
    db.commit()
    db.close()

    response = client.get("/meetings/meeting-not-ready/export?format=pdf")
    assert response.status_code == 400
    assert "Meeting is not ready for export" in response.json()["error"]


def test_export_unsupported_format():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-ready-invalid-fmt",
            filename="planning.mp3",
            upload_time=datetime(2026, 8, 31, 10, 0, 0, tzinfo=timezone.utc),
            status="analyzed",
            file_path="planning.mp3",
        )
    )
    db.add(
        MeetingIntelligence(
            id="intel-inv",
            meeting_id="meeting-ready-invalid-fmt",
            summary="A short summary.",
            key_points_json=json.dumps(["Point 1"]),
            decisions_json=json.dumps(["Decision 1"]),
            action_items_json=json.dumps([{"task": "Task 1", "assignee": "Alice", "deadline": "Friday"}]),
            intelligence_path="planning.json",
            model_name="gemini-2.5-flash",
        )
    )
    db.commit()
    db.close()

    response = client.get("/meetings/meeting-ready-invalid-fmt/export?format=html")
    assert response.status_code == 400
    assert "Unsupported export format" in response.json()["error"]


def test_export_pdf_success():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-pdf-ok",
            filename="quarterly_review.mp3",
            upload_time=datetime(2026, 8, 31, 14, 30, 0, tzinfo=timezone.utc),
            status="analyzed",
            file_path="quarterly_review.mp3",
        )
    )
    db.add(
        MeetingIntelligence(
            id="intel-pdf",
            meeting_id="meeting-pdf-ok",
            summary="Reviewed Q3 performance metrics and aligned on Q4 goals.",
            key_points_json=json.dumps([
                "Revenue up 15% quarter over quarter.",
                "Customer satisfaction score reached 92%.",
            ]),
            decisions_json=json.dumps([
                "Adopt new microservice architecture for billing.",
                "Shift weekly syncs to Tuesday mornings.",
            ]),
            action_items_json=json.dumps([
                {"task": "Finalize budget projections", "assignee": "Sarah", "deadline": "Sept 15"},
                {"task": "Draft architecture RFC", "assignee": "Alex", "deadline": "Sept 20"},
                {"task": "Schedule team retrospective", "assignee": None, "deadline": None},
            ]),
            intelligence_path="dummy.json",
            model_name="gemini-2.5-flash",
        )
    )
    db.commit()
    db.close()

    response = client.get("/meetings/meeting-pdf-ok/export?format=pdf")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert response.headers["Content-Disposition"] == 'attachment; filename="meeting_2026-08-31_meeting-pdf-ok.pdf"'

    # Validate valid PDF binary signature
    content = response.content
    assert content.startswith(b"%PDF-")
    assert len(content) > 1000


def test_export_docx_success():
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-docx-ok",
            filename="product_sync.mp3",
            upload_time=datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
            status="analyzed",
            file_path="product_sync.mp3",
        )
    )
    db.add(
        MeetingIntelligence(
            id="intel-docx",
            meeting_id="meeting-docx-ok",
            summary="Agreed on feature release roadmap for autumn.",
            key_points_json=json.dumps(["Beta launch in October."]),
            decisions_json=json.dumps(["Freeze new feature requests by end of week."]),
            action_items_json=json.dumps([
                {"task": "Notify beta participants", "assignee": "David", "deadline": "Oct 1"},
            ]),
            intelligence_path="dummy.json",
            model_name="gemini-2.5-flash",
        )
    )
    db.commit()
    db.close()

    response = client.get("/meetings/meeting-docx-ok/export?format=docx")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert response.headers["Content-Disposition"] == 'attachment; filename="meeting_2026-09-01_meeting-docx-ok.docx"'

    # Verify DOCX can be opened and parsed
    doc = Document(io.BytesIO(response.content))
    doc_text = " ".join([p.text for p in doc.paragraphs])
    assert "Meeting Report: product_sync.mp3" in doc_text
    assert "Agreed on feature release roadmap for autumn." in doc_text
    assert "Beta launch in October." in doc_text


def test_export_indexed_meeting():
    """Verify that meetings in 'indexed' status export without issue."""
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-indexed-ok",
            filename="indexed_discussion.mp3",
            upload_time=datetime(2026, 9, 2, 11, 0, 0, tzinfo=timezone.utc),
            status="indexed",
            file_path="indexed_discussion.mp3",
        )
    )
    db.add(
        MeetingIntelligence(
            id="intel-idx",
            meeting_id="meeting-indexed-ok",
            summary="Indexed meeting intelligence summary.",
            key_points_json=json.dumps(["Indexed knowledge point."]),
            decisions_json=json.dumps(["Indexed decision."]),
            action_items_json=json.dumps([{"task": "Indexed action", "assignee": "Eve", "deadline": "Soon"}]),
            intelligence_path="dummy.json",
            model_name="gemini-2.5-flash",
        )
    )
    db.commit()
    db.close()

    res_pdf = client.get("/meetings/meeting-indexed-ok/export?format=pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.content.startswith(b"%PDF-")

    res_docx = client.get("/meetings/meeting-indexed-ok/export?format=docx")
    assert res_docx.status_code == 200
    assert len(res_docx.content) > 500


def test_export_with_special_characters_and_markup():
    """Ensure characters like <, >, &, quotes do not crash PDF or Word generation."""
    db = TestingSessionLocal()
    db.add(
        Meeting(
            id="meeting-special-chars",
            filename="special_chars_&_quotes.mp3",
            upload_time=datetime(2026, 9, 3, 16, 0, 0, tzinfo=timezone.utc),
            status="analyzed",
            file_path="special.mp3",
        )
    )
    db.add(
        MeetingIntelligence(
            id="intel-special",
            meeting_id="meeting-special-chars",
            summary="Discussed <XML> tags & JSON schemas with 'quoted' terms and 5 > 3 comparisons.",
            key_points_json=json.dumps(["Support for A & B < C"]),
            decisions_json=json.dumps(["Use standard & safe parsers"]),
            action_items_json=json.dumps([
                {"task": "Test <input> validation & error boundary", "assignee": "Tom & Jerry", "deadline": "<Tomorrow>"},
            ]),
            intelligence_path="dummy.json",
            model_name="gemini-2.5-flash",
        )
    )
    db.commit()
    db.close()

    res_pdf = client.get("/meetings/meeting-special-chars/export?format=pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.content.startswith(b"%PDF-")

    res_docx = client.get("/meetings/meeting-special-chars/export?format=docx")
    assert res_docx.status_code == 200
    assert len(res_docx.content) > 500
