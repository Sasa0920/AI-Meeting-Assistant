## Knowledge Base & RAG — Feature Specification

## Goal
Convert transcribed and analyzed meetings into a searchable vector knowledge base
using Qdrant and Sentence Transformers, and support natural-language question answering
over previous meetings using Google Gemini with strict source attribution and zero hallucination.

## Steps
1. Add an endpoint to trigger vector indexing for an analyzed meeting:
   POST /meetings/{id}/index
   (Manual trigger — allows indexing to be tested in isolation.)
2. Validate the meeting is ready:
   - Meeting exists (else 404)
   - Meeting status is "analyzed" or "done" (else 400)
   - Transcript and/or intelligence are available (else 400)
3. Load the transcript segments and meeting intelligence (summary, key points, decisions, action items).
4. Chunk the content using a dialogue-aware chunker that preserves:
   - speaker labels
   - start and end timestamps
   - source type ("transcript", "summary", "decision", "action_item")
   - meeting_id and meeting filename
5. Compute dense vector embeddings using Sentence Transformers (`all-MiniLM-L6-v2`).
6. Store vectors and metadata payloads in Qdrant vector database under the configured collection.
7. Update meeting status to "indexed" (or "failed" with processing error recorded).
8. Add an endpoint to query the knowledge base with RAG:
   POST /rag/query
   Request: { "query": "...", "meeting_id": optional_str, "top_k": 5 }
9. Retrieve top-k relevant chunks from Qdrant using vector similarity (cosine distance).
10. Construct prompt context with strict citation format and load prompt from `/prompts/rag_qa.txt`.
11. Query Gemini using LangChain (`langchain-google-genai`).
12. Validate LLM response against Pydantic schema:
    - answer: synthesized answer grounded strictly in context
    - sources: list of cited chunks with meeting_id, filename, speaker, timestamps, text
    - insufficient_evidence: boolean flag set to true if query cannot be answered from context
13. If evidence is insufficient, return an honest message stating evidence is unavailable. Never invent facts.
14. Add a fast semantic search endpoint without LLM generation:
    POST /rag/search
    Request: { "query": "...", "meeting_id": optional_str, "limit": 5 }

## Response Shape

Trigger indexing — success (202, indexing started):
{ "meeting_id": "abc123", "status": "processing" }

Trigger indexing — failure (400, e.g. meeting not analyzed):
{ "error": "Meeting is not ready — current status: uploaded" }

Trigger indexing — failure (404):
{ "error": "Meeting not found" }

RAG Query — success (200):
{
  "query": "Who is fixing the auth bug?",
  "answer": "Speaker 2 is fixing the token refresh authentication bug and will submit the PR by Wednesday end of day.",
  "sources": [
    {
      "meeting_id": "eval-01-sprint",
      "filename": "sprint_sync.mp3",
      "speaker": "Speaker 2",
      "start_time": 10.5,
      "end_time": 25.0,
      "text": "Yes, I can fix the token refresh issue. I will submit the pull request by Wednesday end of day.",
      "score": 0.88
    }
  ],
  "insufficient_evidence": false
}

RAG Query — insufficient evidence (200):
{
  "query": "What is the budget for the new office in Berlin?",
  "answer": "I do not have sufficient information from the indexed meetings to answer this question.",
  "sources": [],
  "insufficient_evidence": true
}

Semantic Search — success (200):
{
  "query": "token refresh",
  "results": [
    {
      "meeting_id": "eval-01-sprint",
      "filename": "sprint_sync.mp3",
      "speaker": "Speaker 2",
      "start_time": 10.5,
      "end_time": 25.0,
      "text": "Yes, I can fix the token refresh issue...",
      "score": 0.88
    }
  ]
}

## Out of scope (handled by other features)
- Audio transcription & diarization (Feature 2) — this feature only indexes content already produced
- Summary and action item extraction (Feature 3) — this feature indexes intelligence already generated
- Web interface (Feature 6) — Search/Ask UI slice is coordinated alongside backend endpoints

This feature sits after Meeting Intelligence (Feature 3) in the pipeline;
it turns already-structured meeting content into a searchable knowledge
base spanning all meetings, rather than one meeting at a time.

## Success criteria
- Given an analyzed meeting, triggering /index successfully chunks,
  embeds, and stores its content in Qdrant, moving status to "indexed"
- Asking a question whose answer exists in an indexed meeting returns a
  correct, grounded answer with the right meeting cited as a source
- Asking a question with no relevant indexed content returns an honest
  declaration that evidence is insufficient (zero hallucination)
- Over 85% answer correctness on the evaluation benchmark dataset
- Retrieval Recall@K > 85% for relevant query context
