import logging
import os
from typing import Any, Optional

# pyrefly: ignore [missing-import]
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError

from app.config import settings
from app.schemas import RAGLLMOutput, RAGQueryResponse, RAGSourceChunk
from app.services.embedding import embed_text
from app.services.vector_store import search_similar_chunks

logger = logging.getLogger(__name__)


def load_rag_prompt() -> str:
    if not os.path.exists(settings.RAG_PROMPT_PATH):
        raise FileNotFoundError(f"RAG prompt file not found at {settings.RAG_PROMPT_PATH}")
    with open(settings.RAG_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def format_context_for_prompt(chunks: list[dict[str, Any]]) -> str:
    """Formats retrieved chunks with strict metadata tags for LLM citation."""
    formatted_pieces: list[str] = []
    for i, c in enumerate(chunks, start=1):
        meeting_id = c.get("meeting_id", "unknown")
        filename = c.get("filename", "unknown")
        speaker = c.get("speaker") or "Unknown"
        start = c.get("start_time")
        end = c.get("end_time")
        source_type = c.get("source_type", "transcript")
        text = c.get("text", "").strip()

        time_str = ""
        if start is not None and end is not None:
            time_str = f" [{start:.1f}s - {end:.1f}s]"

        header = f"[Excerpt {i}] Meeting: {filename} (ID: {meeting_id}) | Speaker: {speaker}{time_str} | Type: {source_type}"
        formatted_pieces.append(f"{header}\n{text}")

    return "\n\n".join(formatted_pieces)


def answer_meeting_query(
    query: str,
    meeting_id: Optional[str] = None,
    top_k: int = 5,
) -> RAGQueryResponse:
    """Answers a natural language query using retrieved meeting excerpts and Gemini."""
    clean_query = query.strip()
    if not clean_query:
        raise ValueError("Query cannot be empty")

    # Step 1: Embed query and search Qdrant
    query_vector = embed_text(clean_query)
    retrieved_chunks = search_similar_chunks(
        query_vector=query_vector,
        meeting_id=meeting_id,
        limit=top_k,
    )

    if not retrieved_chunks:
        logger.info("RAG query produced no matching chunks: query_len=%d meeting_filter=%s", len(clean_query), meeting_id)
        return RAGQueryResponse(
            query=clean_query,
            answer="I do not have sufficient information from the indexed meetings to answer this question.",
            sources=[],
            insufficient_evidence=True,
        )

    # Convert retrieved chunks to schema
    source_chunks = [
        RAGSourceChunk(
            meeting_id=c.get("meeting_id", ""),
            filename=c.get("filename", ""),
            speaker=c.get("speaker"),
            start_time=c.get("start_time"),
            end_time=c.get("end_time"),
            source_type=c.get("source_type", "transcript"),
            text=c.get("text", ""),
            score=c.get("score"),
        )
        for c in retrieved_chunks
    ]

    # Step 2: Build context and prompt
    context_text = format_context_for_prompt(retrieved_chunks)
    prompt_template = load_rag_prompt()
    full_prompt = prompt_template.format(context=context_text, question=clean_query)

    # Step 3: LLM generation with structured output
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.0,
    )
    structured_llm = llm.with_structured_output(RAGLLMOutput)

    max_attempts = 2
    last_exception: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            raw_response = structured_llm.invoke(full_prompt)
            if isinstance(raw_response, RAGLLMOutput):
                result = raw_response
            elif isinstance(raw_response, dict):
                result = RAGLLMOutput.model_validate(raw_response)
            else:
                result = RAGLLMOutput.model_validate(raw_response)

            logger.info(
                "RAG answer generated successfully: model=%s attempt=%d insufficient_evidence=%s sources_count=%d",
                settings.GEMINI_MODEL,
                attempt,
                result.insufficient_evidence,
                len(result.sources),
            )

            # If insufficient evidence, do not present misleading sources
            final_sources = [] if result.insufficient_evidence else (result.sources or source_chunks)

            return RAGQueryResponse(
                query=clean_query,
                answer=result.answer,
                sources=final_sources,
                insufficient_evidence=result.insufficient_evidence,
            )
        except (ValidationError, Exception) as exc:
            last_exception = exc
            logger.warning(
                "RAG answer validation failed: model=%s attempt=%d/%d error_type=%s",
                settings.GEMINI_MODEL,
                attempt,
                max_attempts,
                type(exc).__name__,
            )

    raise ValueError(f"Failed to generate valid RAG answer after {max_attempts} attempts: {type(last_exception).__name__}")


def semantic_search_chunks(
    query: str,
    meeting_id: Optional[str] = None,
    limit: int = 5,
) -> list[RAGSourceChunk]:
    """Performs semantic search over indexed meeting chunks without calling LLM."""
    clean_query = query.strip()
    if not clean_query:
        raise ValueError("Query cannot be empty")

    query_vector = embed_text(clean_query)
    retrieved = search_similar_chunks(
        query_vector=query_vector,
        meeting_id=meeting_id,
        limit=limit,
    )

    return [
        RAGSourceChunk(
            meeting_id=c.get("meeting_id", ""),
            filename=c.get("filename", ""),
            speaker=c.get("speaker"),
            start_time=c.get("start_time"),
            end_time=c.get("end_time"),
            source_type=c.get("source_type", "transcript"),
            text=c.get("text", ""),
            score=c.get("score"),
        )
        for c in retrieved
    ]
