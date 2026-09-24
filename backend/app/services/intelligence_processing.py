import json
import logging
import os
from datetime import datetime, timezone

from app.config import settings
from app.database import SessionLocal
from app.models import Meeting, MeetingIntelligence, Transcript
from app.services.intelligence import (
    extract_meeting_intelligence,
    format_transcript_for_llm,
)

logger = logging.getLogger(__name__)


def process_meeting_intelligence(meeting_id: str) -> None:
    """Execute the meeting intelligence background task for a given meeting."""
    db = SessionLocal()
    intelligence_path = None
    try:
        meeting = db.get(Meeting, meeting_id)
        if meeting is None:
            return

        transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
        if transcript is None:
            raise ValueError(f"Transcript not found for meeting {meeting_id}")

        segments = json.loads(transcript.segments_json)
        formatted_transcript = format_transcript_for_llm(segments)
        intelligence = extract_meeting_intelligence(formatted_transcript)

        os.makedirs(settings.INTELLIGENCE_DIR, exist_ok=True)
        intelligence_path = os.path.join(settings.INTELLIGENCE_DIR, f"{meeting_id}.json")

        action_items_dicts = [item.model_dump() for item in intelligence.action_items]
        intelligence_payload = {
            "meeting_id": meeting_id,
            "status": "analyzed",
            "summary": intelligence.summary,
            "key_points": intelligence.key_points,
            "decisions": intelligence.decisions,
            "action_items": action_items_dicts,
            "model_name": settings.GEMINI_MODEL,
        }

        with open(intelligence_path, "w", encoding="utf-8") as f:
            json.dump(intelligence_payload, f, ensure_ascii=True, indent=2)

        existing = db.query(MeetingIntelligence).filter(MeetingIntelligence.meeting_id == meeting_id).first()
        if existing is not None:
            existing.summary = intelligence.summary
            existing.key_points_json = json.dumps(intelligence.key_points, ensure_ascii=True)
            existing.decisions_json = json.dumps(intelligence.decisions, ensure_ascii=True)
            existing.action_items_json = json.dumps(action_items_dicts, ensure_ascii=True)
            existing.intelligence_path = intelligence_path
            existing.model_name = settings.GEMINI_MODEL
            existing.created_at = datetime.now(timezone.utc)
        else:
            db.add(
                MeetingIntelligence(
                    meeting_id=meeting_id,
                    summary=intelligence.summary,
                    key_points_json=json.dumps(intelligence.key_points, ensure_ascii=True),
                    decisions_json=json.dumps(intelligence.decisions, ensure_ascii=True),
                    action_items_json=json.dumps(action_items_dicts, ensure_ascii=True),
                    intelligence_path=intelligence_path,
                    model_name=settings.GEMINI_MODEL,
                    created_at=datetime.now(timezone.utc),
                )
            )

        meeting.status = "analyzed"
        meeting.processing_error = None
        db.commit()

        logger.info(
            "Meeting intelligence processing completed: meeting_id=%s model=%s status=%s",
            meeting_id,
            settings.GEMINI_MODEL,
            meeting.status,
        )
    except Exception as exc:
        db.rollback()
        meeting = db.get(Meeting, meeting_id)
        if meeting is not None:
            meeting.status = "failed"
            meeting.processing_error = type(exc).__name__
            db.commit()
        if intelligence_path and os.path.exists(intelligence_path):
            os.remove(intelligence_path)
        logger.exception(
            "Meeting intelligence processing failed: meeting_id=%s model=%s error_type=%s",
            meeting_id,
            settings.GEMINI_MODEL,
            type(exc).__name__,
        )
    finally:
        db.close()
