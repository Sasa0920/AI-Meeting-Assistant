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
    has_index: bool = False
    processing_error: str | None = None


class MeetingDetailResponse(BaseModel):
    id: str
    filename: str
    upload_time: str
    status: str
    has_transcript: bool = False
    has_intelligence: bool = False
    has_index: bool = False
    processing_error: str | None = None


class RAGSourceChunk(BaseModel):
    meeting_id: str
    filename: str
    speaker: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    source_type: str = "transcript"
    text: str
    score: float | None = None


class RAGQueryRequest(BaseModel):
    query: str = Field(min_length=1)
    meeting_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class RAGLLMOutput(BaseModel):
    answer: str
    sources: list[RAGSourceChunk] = []
    insufficient_evidence: bool = False


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[RAGSourceChunk] = []
    insufficient_evidence: bool = False


class RAGSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    meeting_id: str | None = None
    limit: int = Field(default=5, ge=1, le=20)


class RAGSearchResponse(BaseModel):
    query: str
    results: list[RAGSourceChunk] = []


class MeetingIndexResponse(BaseModel):
    meeting_id: str
    status: str
    chunks_indexed: int = 0
    collection_name: str | None = None



