import os
import shutil
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Meeting
from app.config import settings

router = APIRouter(prefix="/meetings", tags=["meetings"])

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4"}

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
