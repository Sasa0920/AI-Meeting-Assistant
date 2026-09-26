# pyrefly: ignore [missing-import]
from unittest.mock import MagicMock, patch
import pytest

from app.schemas import RAGLLMOutput, RAGSourceChunk
from app.services.rag import (
    answer_meeting_query,
    format_context_for_prompt,
    semantic_search_chunks,
)


def test_format_context_for_prompt():
    chunks = [
        {
            "meeting_id": "m-100",
            "filename": "sprint.mp3",
            "speaker": "Speaker 1",
            "start_time": 10.0,
            "end_time": 25.0,
            "source_type": "transcript",
            "text": "Let us check the auth module.",
        }
    ]
    formatted = format_context_for_prompt(chunks)
    assert "[Excerpt 1]" in formatted
    assert "Meeting: sprint.mp3 (ID: m-100)" in formatted
    assert "Speaker: Speaker 1 [10.0s - 25.0s]" in formatted
    assert "Let us check the auth module." in formatted


@patch("app.services.rag.embed_text")
@patch("app.services.rag.search_similar_chunks")
def test_answer_meeting_query_empty_knowledge_base(mock_search, mock_embed):
    mock_embed.return_value = [0.1] * 384
    mock_search.return_value = []

    res = answer_meeting_query("What was discussed?")
    assert res.insufficient_evidence is True
    assert "sufficient information" in res.answer.lower()
    assert res.sources == []


@patch("app.services.rag.embed_text")
@patch("app.services.rag.search_similar_chunks")
@patch("app.services.rag.ChatGoogleGenerativeAI")
def test_answer_meeting_query_success(mock_chat, mock_search, mock_embed):
    mock_embed.return_value = [0.1] * 384
    mock_search.return_value = [
        {
            "meeting_id": "m-1",
            "filename": "sprint.mp3",
            "speaker": "Speaker 2",
            "start_time": 12.0,
            "end_time": 20.0,
            "source_type": "transcript",
            "text": "I will fix the auth bug.",
            "score": 0.91,
        }
    ]

    mock_llm_instance = MagicMock()
    mock_structured_llm = MagicMock()
    mock_chat.return_value = mock_llm_instance
    mock_llm_instance.with_structured_output.return_value = mock_structured_llm

    mock_structured_llm.invoke.return_value = RAGLLMOutput(
        answer="Speaker 2 will fix the auth bug.",
        sources=[
            RAGSourceChunk(
                meeting_id="m-1",
                filename="sprint.mp3",
                speaker="Speaker 2",
                start_time=12.0,
                end_time=20.0,
                text="I will fix the auth bug.",
                score=0.91,
            )
        ],
        insufficient_evidence=False,
    )

    res = answer_meeting_query("Who fixes auth?")
    assert res.insufficient_evidence is False
    assert "Speaker 2" in res.answer
    assert len(res.sources) == 1
    assert res.sources[0].meeting_id == "m-1"


@patch("app.services.rag.embed_text")
@patch("app.services.rag.search_similar_chunks")
@patch("app.services.rag.ChatGoogleGenerativeAI")
def test_answer_meeting_query_insufficient_evidence_flag(mock_chat, mock_search, mock_embed):
    mock_embed.return_value = [0.1] * 384
    mock_search.return_value = [
        {
            "meeting_id": "m-1",
            "filename": "sprint.mp3",
            "speaker": "Speaker 1",
            "start_time": 0.0,
            "end_time": 5.0,
            "source_type": "transcript",
            "text": "Welcome everyone.",
            "score": 0.35,
        }
    ]

    mock_llm_instance = MagicMock()
    mock_structured_llm = MagicMock()
    mock_chat.return_value = mock_llm_instance
    mock_llm_instance.with_structured_output.return_value = mock_structured_llm

    mock_structured_llm.invoke.return_value = RAGLLMOutput(
        answer="I do not have sufficient information from the indexed meetings to answer this question.",
        sources=[],
        insufficient_evidence=True,
    )

    res = answer_meeting_query("What is the Berlin budget?")
    assert res.insufficient_evidence is True
    assert res.sources == []
