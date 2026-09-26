import logging
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException

from app.schemas import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGSearchRequest,
    RAGSearchResponse,
)
from app.services.rag import answer_meeting_query, semantic_search_chunks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=RAGQueryResponse)
def query_knowledge_base(request: RAGQueryRequest):
    """Ask a natural-language question across indexed meetings or a specific meeting."""
    try:
        response = answer_meeting_query(
            query=request.query,
            meeting_id=request.meeting_id,
            top_k=request.top_k,
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("RAG query failed unexpectedly: %s", type(e).__name__)
        raise HTTPException(status_code=500, detail="Failed to process question answering query")


@router.post("/search", response_model=RAGSearchResponse)
def search_knowledge_base(request: RAGSearchRequest):
    """Retrieve top-K matching semantic chunks without running LLM generation."""
    try:
        results = semantic_search_chunks(
            query=request.query,
            meeting_id=request.meeting_id,
            limit=request.limit,
        )
        return RAGSearchResponse(query=request.query, results=results)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Semantic search failed unexpectedly: %s", type(e).__name__)
        raise HTTPException(status_code=500, detail="Failed to execute semantic search")
