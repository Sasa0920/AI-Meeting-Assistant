import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/meetingiq")
    # Resolve absolute path for UPLOAD_DIR relative to project root
    # assuming this file is in backend/app/config.py, project root is two levels up
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(PROJECT_ROOT, "data", "raw_audio"))

settings = Settings()
