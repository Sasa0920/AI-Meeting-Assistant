## Report Export — Feature Specification

## Goal
Let a user download a meeting's structured results (summary, key points,
decisions, action items) as a clean, readable PDF or Word document.

## Steps
1. Add an export endpoint:
   GET /meetings/{id}/export?format=pdf
   GET /meetings/{id}/export?format=docx
2. Validate the request:
   - Meeting exists (else 404)
   - Meeting has completed intelligence extraction — status "analyzed"
     or later (else 400)
   - format is one of "pdf" or "docx" (else 400)
3. Gather the report data from existing records:
   - Meeting metadata: date, filename/title
   - Summary (Feature 3)
   - Key points (Feature 3)
   - Decisions (Feature 3)
   - Action items: task, assignee, deadline (Feature 3)
4. Build the document using the requested format's library:
   - PDF: reportlab or weasyprint
   - Word: python-docx
   Layout requirements:
   - Clear heading with meeting date/title
   - Summary as a readable paragraph
   - Key points as a bulleted list
   - Decisions as a bulleted or highlighted list
   - Action items as a table: Task | Assignee | Deadline
   - Consistent, deliberate styling (fonts, spacing) — not raw unstyled
     text, matching the visual quality standard set in
     docs/features/06_web_interface.md
5. Generate the file in memory (avoid leaving temp files on disk where
   possible; if a temp file is used, clean it up after the response is sent).
6. Return the file as a downloadable response with an appropriate
   filename, e.g. meeting_{date}_{meeting_id}.pdf or .docx, and the
   correct content-type header for the format.

## Response shape
Success (200):
Binary file response (PDF or DOCX), with headers:
- Content-Type: application/pdf  (or
  application/vnd.openxmlformats-officedocument.wordprocessingml.document
  for docx)
- Content-Disposition: attachment; filename="meeting_2026-08-31_abc123.pdf"

Failure — meeting not ready (400):
{ "error": "Meeting is not ready for export — current status: processing" }

Failure — invalid format (400):
{ "error": "Unsupported export format. Use 'pdf' or 'docx'." }

Failure — meeting not found (404):
{ "error": "Meeting not found" }

## Out of scope (handled by other features)
- Generating the summary, decisions, and action items themselves
  (Feature 3) — this feature only formats and exports data that
  already exists
- Web interface (Feature 6) — the actual "Export" button and download
  trigger in the UI is covered there; this spec is the backend/API only

This feature is a terminal step in the pipeline — it doesn't feed into
any other feature, it packages existing results for the user to keep
or share outside the app.

## Success criteria
- Requesting ?format=pdf for an analyzed meeting returns a valid PDF
  that opens correctly and contains all required sections
- Requesting ?format=docx for the same meeting returns a valid Word
  document that opens correctly with the same content
- Both formats are clearly and consistently styled — not raw
  unformatted text dumped into the file
- Requesting export for a meeting that isn't analyzed yet returns a
  clear 400 error, not an empty or broken file
- Requesting an invalid format value returns a clear 400 error