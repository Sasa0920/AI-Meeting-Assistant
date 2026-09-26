import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/meetingiq")
    # Resolve absolute path for UPLOAD_DIR relative to project root
    # assuming this file is in backend/app/config.py, project root is two levels up
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(PROJECT_ROOT, "data", "raw_audio"))
    TRANSCRIPT_DIR: str = os.getenv("TRANSCRIPT_DIR", os.path.join(PROJECT_ROOT, "data", "transcripts"))
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "small")
    HUGGINGFACE_TOKEN: str = os.getenv("HUGGINGFACE_TOKEN", "")
    DIARIZATION_MODEL: str = os.getenv("DIARIZATION_MODEL", "pyannote/speaker-diarization-3.1")
    INTELLIGENCE_DIR: str = os.getenv("INTELLIGENCE_DIR", os.path.join(PROJECT_ROOT, "data", "intelligence"))
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    INTELLIGENCE_PROMPT_PATH: str = os.getenv(
        "INTELLIGENCE_PROMPT_PATH", os.path.join(PROJECT_ROOT, "prompts", "meeting_intelligence.txt")
    )
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "meeting_knowledge")
    QDRANT_PATH: str = os.getenv("QDRANT_PATH", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    RAG_PROMPT_PATH: str = os.getenv(
        "RAG_PROMPT_PATH", os.path.join(PROJECT_ROOT, "prompts", "rag_qa.txt")
    )

settings = Settings()
