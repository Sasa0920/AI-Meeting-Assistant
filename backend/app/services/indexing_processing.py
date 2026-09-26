import json
import logging
from datetime import datetime, timezone

from app.config import settings
from app.database import SessionLocal
from app.models import Meeting, MeetingIndex, MeetingIntelligence, Transcript
from app.services.chunking import chunk_meeting
from app.services.embedding import embed_batch
from app.services.vector_store import (
    delete_meeting_points,
    ensure_collection,
    insert_chunks,
)

logger = logging.getLogger(__name__)


def process_meeting_indexing(meeting_id: str) -> None:
    """Execute the vector indexing background task for a given meeting."""
    db = SessionLocal()
    try:
        meeting = db.get(Meeting, meeting_id)
        if meeting is None:
            return

        transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
        if transcript is None:
            raise ValueError(f"Transcript not found for meeting {meeting_id}")

        segments = json.loads(transcript.segments_json)

        intelligence_data = None
        intelligence = db.query(MeetingIntelligence).filter(MeetingIntelligence.meeting_id == meeting_id).first()
        if intelligence is not None:
            intelligence_data = {
                "summary": intelligence.summary,
                "decisions": json.loads(intelligence.decisions_json) if intelligence.decisions_json else [],
                "action_items": json.loads(intelligence.action_items_json) if intelligence.action_items_json else [],
            }

        chunks = chunk_meeting(
            meeting_id=meeting_id,
            filename=meeting.filename,
            segments=segments,
            intelligence=intelligence_data,
        )

        if not chunks:
            raise ValueError(f"No chunks produced for meeting {meeting_id}")

        texts = [c["text"] for c in chunks]
        vectors = embed_batch(texts)

        ensure_collection()
        delete_meeting_points(meeting_id)
        indexed_count = insert_chunks(chunks, vectors)

        existing_index = db.query(MeetingIndex).filter(MeetingIndex.meeting_id == meeting_id).first()
        if existing_index is not None:
            existing_index.chunks_count = indexed_count
            existing_index.collection_name = settings.QDRANT_COLLECTION
            existing_index.embedding_model = settings.EMBEDDING_MODEL
            existing_index.created_at = datetime.now(timezone.utc)
        else:
            db.add(
                MeetingIndex(
                    meeting_id=meeting_id,
                    chunks_count=indexed_count,
                    collection_name=settings.QDRANT_COLLECTION,
                    embedding_model=settings.EMBEDDING_MODEL,
                    created_at=datetime.now(timezone.utc),
                )
            )

        meeting.status = "indexed"
        meeting.processing_error = None
        db.commit()

        logger.info(
            "Meeting indexing completed successfully: meeting_id=%s chunks_indexed=%d model=%s status=%s",
            meeting_id,
            indexed_count,
            settings.EMBEDDING_MODEL,
            meeting.status,
        )
    except Exception as exc:
        db.rollback()
        meeting = db.get(Meeting, meeting_id)
        if meeting is not None:
            meeting.status = "failed"
            meeting.processing_error = type(exc).__name__
            db.commit()
        logger.exception(
            "Meeting indexing failed: meeting_id=%s model=%s error_type=%s",
            meeting_id,
            settings.EMBEDDING_MODEL,
            type(exc).__name__,
        )
    finally:
        db.close()
