## Meeting Intelligence — Feature Specification

## Goal
Convert a meeting's speaker-attributed transcript into structured business
information — a summary, key discussion points, decisions made, and action
items with assignees and deadlines — all from a single LLM call.

## Steps
1. Add an endpoint to trigger this stage for a transcribed meeting:
   POST /meetings/{id}/intelligence
   (Manual trigger for now — not automatic after transcription — so this
   stage can be built and tested in isolation.)
2. Validate the meeting is ready:
   - Meeting exists (else 404)
   - Meeting status is "done" (transcription finished) (else 400)
   - A transcript is actually available for this meeting (else 400)
3. Load the speaker-attributed transcript saved in Feature 2.
4. Build a prompt (stored in /prompts/, not hardcoded) instructing Gemini
   to return one structured JSON object containing:
   - summary: a concise paragraph summarizing the meeting
   - key_points: a list of main discussion topics
   - decisions: a list of decisions explicitly made
   - action_items: a list of { task, assignee, deadline } — null where
     assignee or deadline isn't mentioned
5. Send the transcript + prompt to Gemini in a single call — do not make
   separate calls for summary, key points, decisions, and action items.
6. Validate Gemini's response against a Pydantic schema. If the response
   is malformed or missing required fields, do not save it — retry once,
   or mark the meeting as "failed" with a clear reason logged.
7. Save the validated result — a database record (e.g. a
   MeetingIntelligence table linked to the meeting) and/or a JSON file,
   matching how the transcript was stored in Feature 2.
8. Update the meeting's status to reflect this stage is complete (e.g.
   "done" -> "analyzed"), or "failed" if the step could not complete.
9. Add an endpoint to retrieve the result:
   GET /meetings/{id}/intelligence

## Response shape
Trigger processing — success (202, processing started):
{ "meeting_id": "abc123", "status": "processing" }

Trigger processing — failure (400, e.g. transcript not ready):
{ "error": "Meeting is not ready — current status: processing" }

Trigger processing — failure (404):
{ "error": "Meeting not found" }

Get intelligence — success (200):
{
  "meeting_id": "abc123",
  "status": "analyzed",
  "summary": "The team discussed slow database queries on the reports page...",
  "key_points": ["Reports page performance", "Missing database index", "Caching vs. query optimization"],
  "decisions": ["Optimize queries instead of adding caching, for this quarter"],
  "action_items": [
    { "task": "Add index on meeting_id column", "assignee": "Speaker B", "deadline": "today" },
    { "task": "Fix transcripts table join", "assignee": "Speaker C", "deadline": "Thursday" }
  ]
}

Get intelligence — not ready yet (200):
{ "meeting_id": "abc123", "status": "processing" }

Get intelligence — failure (404 or 500):
{ "error": "Intelligence result not found" }
or
{ "error": "Processing failed" }

## Out of scope (handled by other features)
- Transcription & diarization (Feature 2) — this feature only consumes an
  already-finished transcript, it does not produce one
- Embeddings / RAG search over meeting content (Feature 4) — the
  summary/action items are stored here, not yet indexed for search
- Web interface (Feature 6) — this is a backend/API spec only

This feature sits between Transcription (Feature 2) and Knowledge Base/RAG
(Feature 4) in the pipeline; it turns raw transcript text into the
structured business information the rest of the product is built around.

## Success criteria
- Given a meeting with status "done", triggering /intelligence returns a
  result containing all four pieces: summary, key points, decisions, and
  action items
- Action items correctly capture assignee and deadline on test meetings
  that explicitly state them (per the recorded/TTS test scripts)
- Malformed or incomplete LLM output is caught by schema validation and
  never saved as if it were valid
- Action item extraction precision > 80% against the known test scripts
- GET /meetings/{id}/intelligence returns the result in the shape defined
  above once processing is done