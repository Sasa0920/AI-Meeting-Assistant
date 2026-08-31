# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, DateTime
from app.database import Base
import uuid
from datetime import datetime, timezone

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    upload_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, nullable=False, default="uploaded")
    file_path = Column(String, nullable=False)
