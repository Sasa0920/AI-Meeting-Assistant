## Meeting Audio/Video Upload — Feature Specification

## Goal
Allow a user to upload a meeting recording and receive a meeting ID to
track it through the rest of the pipeline.

## Steps
1. Create a database table to store meeting info: meeting ID, filename,
   upload time, status (uploaded/processing/done/failed), file path.
2. Create an API endpoint: POST /meetings/upload
3. Validate the file before accepting:
   - Is it an audio/video file? (.mp3, .wav, .m4a, .mp4)
   - Is it too large? (limit: 2GB)
   - Is it empty or corrupted?
   - On any failure, return a clear error, don't crash.
4. Save the file to /data/raw_audio/, named using the meeting ID.
5. Write a row into the meetings table with status "uploaded".
6. Return a response to the user.

## Response shape
Success (200):
{ "meeting_id": "abc123", "status": "uploaded", "message": "File received successfully" }

Failure (400):
{ "error": "Unsupported file type" }

## Out of scope (handled by other features)
- Transcription (Feature 2) — this feature only stores the file, doesn't process it
- Web interface (Feature 6) — this is a backend/API spec only

This feature is the entry point to the pipeline; downstream stages (transcription, meeting intelligence, RAG) are documented separately in their own feature specs.

## Success criteria
- Valid file → returns 200 with a real meeting_id, file appears in
  /data/raw_audio/, row appears in meetings table with status "uploaded"
- Invalid file type/size/empty file → returns 400 with a clear error,
  nothing gets saved