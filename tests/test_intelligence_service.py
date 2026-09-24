from unittest.mock import MagicMock, patch
import pytest
from pydantic import ValidationError

# pyrefly: ignore [missing-import]
from app.schemas import ActionItem, MeetingIntelligenceOutput
# pyrefly: ignore [missing-import]
from app.services.intelligence import (
    extract_meeting_intelligence,
    format_transcript_for_llm,
    load_intelligence_prompt,
)


def test_format_transcript_for_llm():
    segments = [
        {"speaker": "Speaker 1", "text": "Good morning everyone."},
        {"speaker": "Speaker 2", "text": "Morning! Let's review the roadmap."},
        {"speaker": "Speaker 1", "text": "Sounds good."},
        {"speaker": "Speaker 3", "text": "   "},  # Empty text should be ignored
    ]
    formatted = format_transcript_for_llm(segments)
    expected = (
        "Speaker 1: Good morning everyone.\n"
        "Speaker 2: Morning! Let's review the roadmap.\n"
        "Speaker 1: Sounds good."
    )
    assert formatted == expected


def test_format_transcript_for_llm_defaults_unknown_speaker():
    segments = [{"text": "Hello without speaker"}]
    formatted = format_transcript_for_llm(segments)
    assert formatted == "Unknown: Hello without speaker"


def test_load_intelligence_prompt_success():
    prompt = load_intelligence_prompt()
    assert "{transcript}" in prompt
    assert "summary" in prompt
    assert "action_items" in prompt


def test_extract_meeting_intelligence_empty_transcript():
    with pytest.raises(ValueError, match="Formatted transcript is empty"):
        extract_meeting_intelligence("   ")


def test_extract_meeting_intelligence_success():
    mock_output = MeetingIntelligenceOutput(
        summary="The team discussed the upcoming release roadmap and agreed on target dates.",
        key_points=["Release roadmap", "QA testing phase"],
        decisions=["Ship beta on Friday"],
        action_items=[
            ActionItem(task="Deploy beta build", assignee="Speaker 1", deadline="Friday"),
            ActionItem(task="Write release notes", assignee=None, deadline=None),
        ],
    )

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = mock_output

    with patch("app.services.intelligence.ChatGoogleGenerativeAI") as mock_chat_cls:
        mock_chat_instance = MagicMock()
        mock_chat_cls.return_value = mock_chat_instance
        mock_chat_instance.with_structured_output.return_value = mock_chain

        result = extract_meeting_intelligence("Speaker 1: Let's deploy Friday.")

        assert result.summary == mock_output.summary
        assert result.key_points == ["Release roadmap", "QA testing phase"]
        assert result.decisions == ["Ship beta on Friday"]
        assert len(result.action_items) == 2
        assert result.action_items[0].assignee == "Speaker 1"
        assert result.action_items[0].deadline == "Friday"
        assert result.action_items[1].assignee is None
        assert result.action_items[1].deadline is None


def test_extract_meeting_intelligence_retry_on_first_failure():
    mock_output = MeetingIntelligenceOutput(
        summary="Meeting summary",
        key_points=["Topic A"],
        decisions=["Decision A"],
        action_items=[],
    )

    mock_chain = MagicMock()
    # First invoke raises a validation error or general exception, second succeeds
    mock_chain.invoke.side_effect = [ValueError("Malformed output"), mock_output]

    with patch("app.services.intelligence.ChatGoogleGenerativeAI") as mock_chat_cls:
        mock_chat_instance = MagicMock()
        mock_chat_cls.return_value = mock_chat_instance
        mock_chat_instance.with_structured_output.return_value = mock_chain

        result = extract_meeting_intelligence("Speaker 1: Hello world")

        assert result.summary == "Meeting summary"
        assert mock_chain.invoke.call_count == 2


def test_extract_meeting_intelligence_fails_after_all_retries(caplog):
    mock_chain = MagicMock()
    mock_chain.invoke.side_effect = [ValueError("Malformed 1"), ValueError("Malformed 2")]

    with patch("app.services.intelligence.ChatGoogleGenerativeAI") as mock_chat_cls:
        mock_chat_instance = MagicMock()
        mock_chat_cls.return_value = mock_chat_instance
        mock_chat_instance.with_structured_output.return_value = mock_chain

        with pytest.raises(ValueError, match="Failed to extract valid meeting intelligence after 2 attempts"):
            extract_meeting_intelligence("Speaker 1: Secret discussions about confidential projects")

        # Verify no transcript content appears in log messages (metadata only rule)
        for record in caplog.records:
            assert "Secret discussions" not in record.message
