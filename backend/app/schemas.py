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


class ActionItem(BaseModel):
    task: str
    assignee: str | None = None
    deadline: str | None = None


class MeetingIntelligenceOutput(BaseModel):
    summary: str
    key_points: list[str]
    decisions: list[str]
    action_items: list[ActionItem]


class MeetingIntelligenceResponse(BaseModel):
    meeting_id: str
    status: str
    summary: str
    key_points: list[str]
    decisions: list[str]
    action_items: list[ActionItem]


class MeetingListItem(BaseModel):
    id: str
    filename: str
    upload_time: str
    status: str
    has_transcript: bool = False
    has_intelligence: bool = False
    processing_error: str | None = None


class MeetingDetailResponse(BaseModel):
    id: str
    filename: str
    upload_time: str
    status: str
    has_transcript: bool = False
    has_intelligence: bool = False
    processing_error: str | None = None



