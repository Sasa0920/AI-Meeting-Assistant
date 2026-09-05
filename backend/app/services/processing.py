import json
import logging
import os
from datetime import datetime, timezone

from app.config import settings
from app.database import SessionLocal
from app.models import Meeting, Transcript
from app.services.diarization import diarize_audio
from app.services.merge import merge_transcript
from app.services.transcription import transcribe_audio

logger = logging.getLogger(__name__)


def process_meeting(meeting_id: str) -> None:
    db = SessionLocal()
    transcript_path = None
    try:
        meeting = db.get(Meeting, meeting_id)
        if meeting is None:
            return

        transcript_path = os.path.join(settings.TRANSCRIPT_DIR, f"{meeting_id}.json")
        transcription = transcribe_audio(meeting.file_path, settings.WHISPER_MODEL)
        diarization = diarize_audio(
            meeting.file_path,
            settings.DIARIZATION_MODEL,
            settings.HUGGINGFACE_TOKEN,
        )
        segments = merge_transcript(transcription, diarization)

        os.makedirs(settings.TRANSCRIPT_DIR, exist_ok=True)
        with open(transcript_path, "w", encoding="utf-8") as transcript_file:
            json.dump(segments, transcript_file, ensure_ascii=True, indent=2)

        existing = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
        if existing is not None:
            db.delete(existing)
        db.add(
            Transcript(
                meeting_id=meeting_id,
                transcript_path=transcript_path,
                segments_json=json.dumps(segments, ensure_ascii=True),
                whisper_model=settings.WHISPER_MODEL,
                diarization_model=settings.DIARIZATION_MODEL,
                created_at=datetime.now(timezone.utc),
            )
        )
        meeting.status = "done"
        db.commit()
        logger.info("Meeting processing completed: meeting_id=%s whisper_model=%s", meeting_id, settings.WHISPER_MODEL)
    except Exception as exc:
        db.rollback()
        meeting = db.get(Meeting, meeting_id)
        if meeting is not None:
            meeting.status = "failed"
            meeting.processing_error = type(exc).__name__
            db.commit()
        if transcript_path and os.path.exists(transcript_path):
            os.remove(transcript_path)
        logger.exception(
            "Meeting processing failed: meeting_id=%s whisper_model=%s error_type=%s",
            meeting_id,
            settings.WHISPER_MODEL,
            type(exc).__name__,
        )
    finally:
        db.close()
