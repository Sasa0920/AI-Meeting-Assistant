import json
import logging
import os
from typing import Any

# pyrefly: ignore [missing-import]
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError

from app.config import settings
from app.schemas import MeetingIntelligenceOutput

logger = logging.getLogger(__name__)


def format_transcript_for_llm(segments: list[dict[str, Any]]) -> str:
    """Format speaker-attributed segments into a readable dialogue string."""
    formatted_lines: list[str] = []
    for segment in segments:
        speaker = segment.get("speaker", "Unknown")
        text = segment.get("text", "").strip()
        if text:
            formatted_lines.append(f"{speaker}: {text}")
    return "\n".join(formatted_lines)


def load_intelligence_prompt() -> str:
    """Load the prompt template from the configured prompt path."""
    if not os.path.exists(settings.INTELLIGENCE_PROMPT_PATH):
        raise FileNotFoundError(f"Intelligence prompt file not found at {settings.INTELLIGENCE_PROMPT_PATH}")
    with open(settings.INTELLIGENCE_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def extract_meeting_intelligence(formatted_transcript: str) -> MeetingIntelligenceOutput:
    """Extract meeting intelligence using Gemini with structured output and 1 retry on validation failure.
    
    Ensures that no transcript content is logged — only metadata.
    """
    if not formatted_transcript.strip():
        raise ValueError("Formatted transcript is empty")

    prompt_template = load_intelligence_prompt()
    full_prompt = prompt_template.format(transcript=formatted_transcript)

    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.0,
    )
    structured_llm = llm.with_structured_output(MeetingIntelligenceOutput)

    max_attempts = 2
    last_exception: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = structured_llm.invoke(full_prompt)
            if isinstance(response, MeetingIntelligenceOutput):
                result = response
            elif isinstance(response, dict):
                result = MeetingIntelligenceOutput.model_validate(response)
            else:
                result = MeetingIntelligenceOutput.model_validate(response)

            logger.info(
                "Meeting intelligence extraction succeeded: model=%s attempt=%d summary_length=%d key_points_count=%d decisions_count=%d action_items_count=%d",
                settings.GEMINI_MODEL,
                attempt,
                len(result.summary),
                len(result.key_points),
                len(result.decisions),
                len(result.action_items),
            )
            return result
        except (ValidationError, Exception) as exc:
            last_exception = exc
            logger.warning(
                "Meeting intelligence extraction failed: model=%s attempt=%d/%d error_type=%s",
                settings.GEMINI_MODEL,
                attempt,
                max_attempts,
                type(exc).__name__,
            )

    raise ValueError(f"Failed to extract valid meeting intelligence after {max_attempts} attempts: {type(last_exception).__name__}")
