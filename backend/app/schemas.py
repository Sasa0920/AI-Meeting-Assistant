from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    speaker: str
    start: float = Field(ge=0)
    end: float = Field(ge=0)
    text: str


class ProcessResponse(BaseModel):
    meeting_id: str
    status: str


class TranscriptResponse(BaseModel):
    meeting_id: str
    status: str
    transcript: list[TranscriptSegment] | None = None
