# pyrefly: ignore [missing-import]
import pytest

from app.services.chunking import (
    chunk_intelligence,
    chunk_meeting,
    chunk_transcript_segments,
)


def test_chunk_transcript_segments_preserves_metadata():
    segments = [
        {"speaker": "Speaker 1", "start": 0.0, "end": 4.5, "text": "Hello team, let us review the sprint."},
        {"speaker": "Speaker 1", "start": 4.5, "end": 9.0, "text": "We need to fix the auth bug first."},
        {"speaker": "Speaker 2", "start": 9.5, "end": 14.0, "text": "I can handle that token refresh issue."},
    ]

    chunks = chunk_transcript_segments(
        meeting_id="m-123",
        filename="sprint.mp3",
        segments=segments,
        max_chunk_chars=1000,
    )

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk["meeting_id"] == "m-123"
    assert chunk["filename"] == "sprint.mp3"
    assert chunk["start_time"] == 0.0
    assert chunk["end_time"] == 14.0
    assert chunk["source_type"] == "transcript"
    assert "Speaker 1: Hello team" in chunk["text"]
    assert "Speaker 2: I can handle" in chunk["text"]
    assert chunk["speaker"] == "Multiple Speakers"


def test_chunk_transcript_single_speaker():
    segments = [
        {"speaker": "Speaker 1", "start": 0.0, "end": 3.0, "text": "First comment."},
        {"speaker": "Speaker 1", "start": 3.5, "end": 6.0, "text": "Second comment."},
    ]

    chunks = chunk_transcript_segments(
        meeting_id="m-123",
        filename="sprint.mp3",
        segments=segments,
    )

    assert len(chunks) == 1
    assert chunks[0]["speaker"] == "Speaker 1"


def test_chunk_intelligence_sections():
    intel = {
        "summary": "This was a planning meeting.",
        "decisions": ["Deploy on Friday", "Skip Redis"],
        "action_items": [
            {"task": "Write docs", "assignee": "Alice", "deadline": "tomorrow"},
        ],
    }

    chunks = chunk_intelligence("m-123", "sprint.mp3", intel)
    assert len(chunks) == 3

    types = {c["source_type"] for c in chunks}
    assert types == {"summary", "decision", "action_item"}

    decision_chunk = next(c for c in chunks if c["source_type"] == "decision")
    assert "Deploy on Friday" in decision_chunk["text"]
    assert "Skip Redis" in decision_chunk["text"]


def test_chunk_meeting_combined():
    segments = [{"speaker": "Speaker 1", "start": 0.0, "end": 2.0, "text": "Sync up."}]
    intel = {"summary": "Short sync."}

    chunks = chunk_meeting("m-123", "test.mp3", segments, intel)
    assert len(chunks) == 2
    assert chunks[0]["source_type"] == "transcript"
    assert chunks[1]["source_type"] == "summary"
