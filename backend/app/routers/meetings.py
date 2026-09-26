import os
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, BackgroundTasks, File, UploadFile, HTTPException, Depends
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Meeting, Transcript, MeetingIntelligence, MeetingIndex
from app.config import settings
from app.schemas import (
    ActionItem,
    MeetingDetailResponse,
    MeetingIntelligenceResponse,
    MeetingListItem,
    ProcessResponse,
    TranscriptResponse,
    TranscriptSegment,
)
from app.services.processing import process_meeting
from app.services.intelligence_processing import process_meeting_intelligence
from app.services.indexing_processing import process_meeting_indexing
import json

router = APIRouter(prefix="/meetings", tags=["meetings"])

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4"}


@router.post("/{meeting_id}/process", response_model=ProcessResponse, status_code=202)
def start_processing(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.status not in {"uploaded", "failed"}:
        raise HTTPException(status_code=400, detail="Meeting has already been processed or is processing")
    if not meeting.file_path or not os.path.isfile(meeting.file_path):
        meeting.status = "failed"
        meeting.processing_error = "Meeting audio file not found"
        db.commit()
        raise HTTPException(status_code=400, detail="Meeting audio file not found")

    meeting.status = "processing"
    meeting.processing_error = None
    db.commit()
    background_tasks.add_task(process_meeting, meeting_id)
    return {"meeting_id": meeting_id, "status": "processing"}


@router.get(
    "/{meeting_id}/transcript",
    response_model=TranscriptResponse,
    response_model_exclude_none=True,
)
def get_transcript(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    if transcript is None:
        if meeting.status == "processing":
            return {"meeting_id": meeting_id, "status": "processing"}
        if meeting.status == "failed":
            raise HTTPException(status_code=500, detail="Processing failed")
        raise HTTPException(status_code=404, detail="Transcript not found")

    segments = [TranscriptSegment.model_validate(segment) for segment in json.loads(transcript.segments_json)]
    return {
        "meeting_id": meeting_id,
        "status": "transcribed" if meeting.status in ("done", "analyzed", "indexed") else meeting.status,
        "transcript": segments,
    }


@router.post("/{meeting_id}/intelligence", response_model=ProcessResponse, status_code=202)
def start_intelligence(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.status == "processing":
        raise HTTPException(status_code=400, detail="Meeting is not ready — current status: processing")
    if meeting.status not in {"done", "analyzed", "indexed", "failed"}:
        raise HTTPException(status_code=400, detail=f"Meeting is not ready — current status: {meeting.status}")

    transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    if transcript is None:
        raise HTTPException(status_code=400, detail="Transcript not found for this meeting")

    meeting.status = "processing"
    meeting.processing_error = None
    db.commit()
    background_tasks.add_task(process_meeting_intelligence, meeting_id)
    return {"meeting_id": meeting_id, "status": "processing"}


@router.get(
    "/{meeting_id}/intelligence",
    response_model=MeetingIntelligenceResponse | ProcessResponse,
)
def get_intelligence(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    intelligence = db.query(MeetingIntelligence).filter(MeetingIntelligence.meeting_id == meeting_id).first()
    if intelligence is None:
        if meeting.status == "processing":
            return ProcessResponse(meeting_id=meeting_id, status="processing")
        if meeting.status == "failed":
            raise HTTPException(status_code=500, detail="Processing failed")
        raise HTTPException(status_code=404, detail="Intelligence result not found")

    key_points = json.loads(intelligence.key_points_json)
    decisions = json.loads(intelligence.decisions_json)
    action_items = [ActionItem.model_validate(item) for item in json.loads(intelligence.action_items_json)]

    return MeetingIntelligenceResponse(
        meeting_id=meeting_id,
        status="analyzed",
        summary=intelligence.summary,
        key_points=key_points,
        decisions=decisions,
        action_items=action_items,
    )


@router.post("/{meeting_id}/index", response_model=ProcessResponse, status_code=202)
def start_indexing(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.status == "processing":
        raise HTTPException(status_code=400, detail="Meeting is not ready — current status: processing")
    if meeting.status not in {"analyzed", "done", "indexed", "failed"}:
        raise HTTPException(status_code=400, detail=f"Meeting is not ready — current status: {meeting.status}")

    transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    if transcript is None:
        raise HTTPException(status_code=400, detail="Transcript not found for this meeting")

    meeting.status = "processing"
    meeting.processing_error = None
    db.commit()
    background_tasks.add_task(process_meeting_indexing, meeting_id)
    return {"meeting_id": meeting_id, "status": "processing"}


@router.post("/upload")
def upload_meeting(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # Read the first byte to check if the file is empty
    first_byte = file.file.read(1)
    if not first_byte:
        raise HTTPException(status_code=400, detail="Empty file")
    
    # Move the cursor back to the beginning of the file
    file.file.seek(0)
    
    # Validation for size could be implemented by checking `os.fstat` of the spooled file,
    # but reading as chunks and checking accumulated size is safer if it's completely in memory.
    # SpooledTemporaryFile might not have an easy fstat. We'll track it while saving.
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Create DB record to get an ID
    meeting = Meeting(filename=file.filename, status="uploaded", file_path="")
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    
    # Save the file
    file_path = os.path.join(settings.UPLOAD_DIR, meeting.id + ext)
    
    try:
        size = 0
        MAX_SIZE = 2 * 1024 * 1024 * 1024 # 2 GB
        with open(file_path, "wb") as f:
            while chunk := file.file.read(1024 * 1024): # Read in 1MB chunks
                size += len(chunk)
                if size > MAX_SIZE:
                    raise ValueError("File exceeds 2GB limit")
                f.write(chunk)
                
        # Update the DB record with file path
        meeting.file_path = file_path
        db.commit()
        
    except ValueError as e:
        # File was too large
        db.delete(meeting)
        db.commit()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Generic fallback
        db.delete(meeting)
        db.commit()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Internal server error while saving file")
    finally:
        file.file.close()
        
    return {
        "meeting_id": meeting.id,
        "status": meeting.status,
        "message": "File received successfully"
    }


@router.get("", response_model=list[MeetingListItem])
@router.get("/", response_model=list[MeetingListItem], include_in_schema=False)
def list_meetings(db: Session = Depends(get_db)):
    meetings = db.query(Meeting).order_by(Meeting.upload_time.desc()).all()
    
    # Query meeting IDs with transcripts, intelligence, and index in batch
    transcript_meeting_ids = {
        row[0] for row in db.query(Transcript.meeting_id).all()
    }
    intelligence_meeting_ids = {
        row[0] for row in db.query(MeetingIntelligence.meeting_id).all()
    }
    index_meeting_ids = {
        row[0] for row in db.query(MeetingIndex.meeting_id).all()
    }

    result = []
    for m in meetings:
        upload_time_str = m.upload_time.isoformat() if m.upload_time else ""
        result.append(
            MeetingListItem(
                id=m.id,
                filename=m.filename,
                upload_time=upload_time_str,
                status=m.status,
                has_transcript=m.id in transcript_meeting_ids,
                has_intelligence=m.id in intelligence_meeting_ids,
                has_index=m.id in index_meeting_ids,
                processing_error=m.processing_error,
            )
        )
    return result


@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
def get_meeting(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    has_transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first() is not None
    has_intelligence = db.query(MeetingIntelligence).filter(MeetingIntelligence.meeting_id == meeting_id).first() is not None
    has_index = db.query(MeetingIndex).filter(MeetingIndex.meeting_id == meeting_id).first() is not None
    upload_time_str = meeting.upload_time.isoformat() if meeting.upload_time else ""

    return MeetingDetailResponse(
        id=meeting.id,
        filename=meeting.filename,
        upload_time=upload_time_str,
        status=meeting.status,
        has_transcript=has_transcript,
        has_intelligence=has_intelligence,
        has_index=has_index,
        processing_error=meeting.processing_error,
    )
