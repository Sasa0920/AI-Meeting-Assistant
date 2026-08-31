## Web Interface — Feature Specification

## Goal
Provide a web-based UI for uploading, viewing, searching, and managing
meetings — built incrementally, one screen per backend feature, rather
than as a single feature at the end.

## Approach: build alongside each backend feature
Instead of building the full UI after every backend feature is done, add
one screen (or one section of a screen) each time a backend feature
becomes usable. This gives visible, testable progress at every stage
instead of only at the very end.

| Backend feature | UI added alongside it |
|---|---|
| 01 Meeting Upload | Upload page: file picker, upload button, status after upload |
| 02 Transcription & Diarization | Transcript view: speaker-labeled text for a meeting |
| 03 Meeting Intelligence | Summary view: key points, decisions, action items on the meeting page |
| 04 Knowledge Base & RAG | Search/ask page: natural-language question box + answers |
| 05 Report Export | Export button on the meeting page (download PDF/Word) |
| — | Meetings list/dashboard: ties everything together, built once enough pages exist to link |

## Screens (final result once all slices are built)
1. **Upload page** — drag-and-drop or file picker, upload progress, success/error state
2. **Meetings dashboard** — list of past meetings with status, date, quick actions
3. **Meeting detail page** — tabs or sections for transcript, summary, action items, export
4. **Search / Ask page** — natural-language question box, answers with source meeting references

## Design Direction — making it look intentional, not generic

The goal is a UI that looks like a considered product, not a default
Bootstrap/Material template. A few concrete choices to commit to, rather
than leaving style undecided:

### Visual identity
- Pick ONE accent color with meaning — e.g. a deep indigo or teal for an
  "intelligence/focus" feel, rather than a generic blue. Use it sparingly
  (buttons, active states, highlights) against a mostly neutral palette
  (off-white or near-black background, greys for structure).
- Avoid default-looking rounded cards with drop shadows everywhere — pick
  either a flat, bordered style OR a soft-shadow style, not both mixed.
- Use one distinctive typeface pairing: a clean sans-serif for UI text
  (e.g. Inter, Manrope) — avoid the default system font stack, which
  reads as "unstyled."

### Layout personality
- Meeting transcripts are inherently document-like — lean into that:
  generous whitespace, readable line length, clear speaker labels (color
  or avatar-coded per speaker) rather than a cramped chat-bubble look.
- Action items and decisions should visually stand out from general
  summary text — e.g. a distinct card or colored left-border, not just
  another paragraph.
- The search/ask page should feel closer to a focused search tool than a
  generic chatbot — a prominent single input, not a full chat thread UI,
  since this is Q&A over documents, not a conversation.

### What to avoid
- Default unstyled HTML form elements
- Every card looking identical regardless of content type (transcript vs.
  summary vs. action item should each have a distinct visual treatment)
- Overusing gradients, glassmorphism, or trend-driven effects that date
  quickly and distract from a business-tool feel

## Out of scope (handled by other features)
- Backend logic for each feature (transcription, summarization, RAG) — this
  spec only covers how results are displayed and interacted with
- Authentication/user accounts — not in current project scope

## Success criteria
- Each UI slice is added and tested against its live backend endpoint
  (not mock data) within the same session the backend feature is built
- The finished interface is visually consistent across all screens (same
  accent color, spacing, and typography throughout)
- A reviewer looking at the UI can tell it was designed deliberately,
  not left at framework defaults