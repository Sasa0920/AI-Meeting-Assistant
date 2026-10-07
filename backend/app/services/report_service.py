import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.models import Meeting, MeetingIntelligence
from app.services.export.docx_exporter import generate_docx_report
from app.services.export.pdf_exporter import generate_pdf_report


class ReportExportError(Exception):
    """Exception for report export failures."""
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def get_meeting_report_data(meeting_id: str, db: Session) -> Dict[str, Any]:
    """Retrieve and validate report data for an analyzed meeting."""
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise ReportExportError(404, "Meeting not found")

    intelligence = (
        db.query(MeetingIntelligence)
        .filter(MeetingIntelligence.meeting_id == meeting_id)
        .first()
    )

    if intelligence is None:
        raise ReportExportError(
            400,
            f"Meeting is not ready for export — current status: {meeting.status}",
        )

    date_str = (
        meeting.upload_time.strftime("%Y-%m-%d")
        if meeting.upload_time
        else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )

    key_points = json.loads(intelligence.key_points_json) if intelligence.key_points_json else []
    decisions = json.loads(intelligence.decisions_json) if intelligence.decisions_json else []
    action_items = json.loads(intelligence.action_items_json) if intelligence.action_items_json else []

    return {
        "meeting_id": meeting.id,
        "filename": meeting.filename,
        "date_str": date_str,
        "summary": intelligence.summary,
        "key_points": key_points,
        "decisions": decisions,
        "action_items": action_items,
    }


def export_meeting_report(meeting_id: str, format_str: str, db: Session) -> Tuple[io.BytesIO, str, str]:
    """Export meeting intelligence report as PDF or Word document in-memory.

    Returns:
        (buffer, filename, content_type)
    """
    clean_format = (format_str or "").strip().lower()
    if clean_format not in {"pdf", "docx"}:
        raise ReportExportError(400, "Unsupported export format. Use 'pdf' or 'docx'.")

    data = get_meeting_report_data(meeting_id, db)
    date_str = data["date_str"]
    download_filename = f"meeting_{date_str}_{meeting_id}.{clean_format}"

    if clean_format == "pdf":
        buffer = generate_pdf_report(data)
        content_type = "application/pdf"
    else:
        buffer = generate_docx_report(data)
        content_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    return buffer, download_filename, content_type
