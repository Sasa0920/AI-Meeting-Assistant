## Transcription & Speaker Diarization — Feature Specification

## Goal
Convert an uploaded meeting's audio into a speaker-attributed transcript —
text of what was said, combined with who said it and when.

## Steps
1. Add an endpoint to trigger processing for an uploaded meeting:
   POST /meetings/{id}/process
   (Manual trigger for now — not automatic after upload — so this stage
   can be built and tested in isolation.)
2. Load the meeting's audio file using its stored file_path.
3. Run Whisper on the audio to get the spoken text with timestamps
   (what was said, and when).
4. Run pyannote.audio on the same audio to get speaker segments with
   timestamps (who spoke, and when) — no knowledge of the words themselves.
5. Merge both results by matching overlapping timestamps, producing a
   single ordered list of { speaker, start, end, text } segments.
6. Save the merged transcript to /data/transcripts/ (as a file) and as a
   database record linked to the meeting.
7. Update the meeting's status: "uploaded" -> "processing" -> "done"
   (or "failed" if any step throws an error).
8. Add an endpoint to retrieve the result:
   GET /meetings/{id}/transcript

## Response shape
Trigger processing — success (202, processing started):
{ "meeting_id": "abc123", "status": "processing" }

Trigger processing — failure (400, e.g. meeting not found or already processed):
{ "error": "Meeting not found" }

Get transcript — success (200):
{
  "meeting_id": "abc123",
  "status": "done",
  "transcript": [
    { "speaker": "Speaker 1", "start": 0.0, "end": 5.2, "text": "Let's discuss the budget" },
    { "speaker": "Speaker 2", "start": 5.2, "end": 9.8, "text": "Sure, I've prepared the numbers" }
  ]
}

Get transcript — not ready yet (200 or 202, still processing):
{ "meeting_id": "abc123", "status": "processing" }

Get transcript — failure (404 or 500):
{ "error": "Transcript not found" }
or
{ "error": "Processing failed" }

## Out of scope (handled by other features)
- Meeting Intelligence: summaries, decisions, action items (Feature 3) —
  this feature only produces the raw speaker-attributed transcript, it
  does not interpret or summarize the content
- Embeddings / RAG search over transcripts (Feature 4) — transcript is
  just stored here, not yet indexed for search
- Web interface (Feature 6) — this is a backend/API spec only

This feature sits between Upload (Feature 1) and Meeting Intelligence
(Feature 3) in the pipeline; it turns a raw audio file into structured,
speaker-labeled text that later features build on.

## Success criteria
- Given a meeting with status "uploaded", triggering /process successfully
  moves it through "processing" to "done" (or to "failed" with a clear
  reason if something breaks)
- The resulting transcript correctly separates at least 2 distinct
  speakers on a test recording with 2+ speakers
- Transcription accuracy > 90% (Word Error Rate) against a known script
  (e.g. one of the recorded/TTS-generated test meetings)
- GET /meetings/{id}/transcript returns the transcript in the shape
  defined above once processing is done
- Processing time stays under 2x the audio's duration