from typing import Any, Optional


def chunk_transcript_segments(
    meeting_id: str,
    filename: str,
    segments: list[dict[str, Any]],
    max_chunk_chars: int = 600,
    overlap_chars: int = 100,
) -> list[dict[str, Any]]:
    """Chunks transcript segments while preserving speaker attribution and timestamps."""
    if not segments:
        return []

    chunks: list[dict[str, Any]] = []
    current_texts: list[str] = []
    current_speakers: list[str] = []
    current_start: Optional[float] = None
    current_end: Optional[float] = None
    current_len = 0
    chunk_idx = 0

    for seg in segments:
        speaker = seg.get("speaker", "Unknown")
        text = seg.get("text", "").strip()
        start = seg.get("start", 0.0)
        end = seg.get("end", 0.0)

        if not text:
            continue

        formatted_line = f"{speaker}: {text}"
        line_len = len(formatted_line)

        if current_len + line_len > max_chunk_chars and current_texts:
            # Emit current chunk
            speaker_label = current_speakers[0] if len(set(current_speakers)) == 1 else "Multiple Speakers"
            combined_text = "\n".join(current_texts)
            chunks.append({
                "meeting_id": meeting_id,
                "filename": filename,
                "speaker": speaker_label,
                "start_time": current_start,
                "end_time": current_end,
                "source_type": "transcript",
                "text": combined_text,
                "chunk_index": chunk_idx,
            })
            chunk_idx += 1

            # Prepare next chunk with possible overlap if configured
            current_texts = []
            current_speakers = []
            current_start = None
            current_end = None
            current_len = 0

        if current_start is None:
            current_start = start
        current_end = end
        current_texts.append(formatted_line)
        current_speakers.append(speaker)
        current_len += line_len

    # Emit final remaining chunk
    if current_texts:
        speaker_label = current_speakers[0] if len(set(current_speakers)) == 1 else "Multiple Speakers"
        combined_text = "\n".join(current_texts)
        chunks.append({
            "meeting_id": meeting_id,
            "filename": filename,
            "speaker": speaker_label,
            "start_time": current_start,
            "end_time": current_end,
            "source_type": "transcript",
            "text": combined_text,
            "chunk_index": chunk_idx,
        })
        chunk_idx += 1

    return chunks


def chunk_intelligence(
    meeting_id: str,
    filename: str,
    intelligence: dict[str, Any],
    start_chunk_idx: int = 0,
) -> list[dict[str, Any]]:
    """Chunks summary, decisions, and action items from meeting intelligence."""
    chunks: list[dict[str, Any]] = []
    idx = start_chunk_idx

    summary = intelligence.get("summary")
    if summary and isinstance(summary, str) and summary.strip():
        chunks.append({
            "meeting_id": meeting_id,
            "filename": filename,
            "speaker": "Executive Summary",
            "start_time": None,
            "end_time": None,
            "source_type": "summary",
            "text": f"Meeting Summary: {summary.strip()}",
            "chunk_index": idx,
        })
        idx += 1

    decisions = intelligence.get("decisions") or []
    if decisions:
        decisions_text = "Decisions Agreed Upon:\n" + "\n".join(f"- {d}" for d in decisions)
        chunks.append({
            "meeting_id": meeting_id,
            "filename": filename,
            "speaker": "Meeting Decisions",
            "start_time": None,
            "end_time": None,
            "source_type": "decision",
            "text": decisions_text,
            "chunk_index": idx,
        })
        idx += 1

    action_items = intelligence.get("action_items") or []
    if action_items:
        items_lines = []
        for item in action_items:
            task = item.get("task", "")
            assignee = item.get("assignee") or "Unassigned"
            deadline = item.get("deadline") or "No deadline specified"
            items_lines.append(f"- Task: {task} | Assignee: {assignee} | Deadline: {deadline}")
        action_text = "Action Items:\n" + "\n".join(items_lines)
        chunks.append({
            "meeting_id": meeting_id,
            "filename": filename,
            "speaker": "Action Items",
            "start_time": None,
            "end_time": None,
            "source_type": "action_item",
            "text": action_text,
            "chunk_index": idx,
        })
        idx += 1

    return chunks


def chunk_meeting(
    meeting_id: str,
    filename: str,
    segments: list[dict[str, Any]],
    intelligence: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """Generates all chunks for a meeting from its transcript and optional intelligence."""
    transcript_chunks = chunk_transcript_segments(meeting_id, filename, segments)
    intel_chunks = []
    if intelligence:
        intel_chunks = chunk_intelligence(
            meeting_id,
            filename,
            intelligence,
            start_chunk_idx=len(transcript_chunks),
        )
    return transcript_chunks + intel_chunks
