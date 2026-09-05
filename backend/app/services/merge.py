from collections import defaultdict
from typing import Any


def _overlap(start: float, end: float, other_start: float, other_end: float) -> float:
    return max(0.0, min(end, other_end) - max(start, other_start))


def _speaker_for_interval(
    start: float,
    end: float,
    diarization: list[dict[str, Any]],
) -> str:
    overlaps = defaultdict(float)
    for segment in diarization:
        overlaps[segment["speaker"]] += _overlap(
            start, end, segment["start"], segment["end"]
        )
    return max(overlaps, key=overlaps.get) if overlaps else "Unknown"


def merge_transcript(
    transcription: list[dict[str, Any]],
    diarization: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    raw_segments = []
    for segment in transcription:
        words = segment.get("words") or []
        if words:
            for word in words:
                text = str(word.get("word", "")).strip()
                if text:
                    raw_segments.append(
                        {
                            "speaker": _speaker_for_interval(
                                float(word["start"]), float(word["end"]), diarization
                            ),
                            "start": float(word["start"]),
                            "end": float(word["end"]),
                            "text": text,
                        }
                    )
        else:
            text = str(segment.get("text", "")).strip()
            if text:
                start = float(segment["start"])
                end = float(segment["end"])
                raw_segments.append(
                    {
                        "speaker": _speaker_for_interval(start, end, diarization),
                        "start": start,
                        "end": end,
                        "text": text,
                    }
                )

    speaker_names = {}
    merged = []
    for segment in sorted(raw_segments, key=lambda item: item["start"]):
        raw_speaker = segment["speaker"]
        if raw_speaker not in speaker_names:
            speaker_names[raw_speaker] = f"Speaker {len(speaker_names) + 1}"
        segment["speaker"] = speaker_names[raw_speaker]
        if (
            merged
            and merged[-1]["speaker"] == segment["speaker"]
            and segment["start"] <= merged[-1]["end"] + 0.5
        ):
            merged[-1]["end"] = max(merged[-1]["end"], segment["end"])
            merged[-1]["text"] = f'{merged[-1]["text"]} {segment["text"]}'.strip()
        else:
            merged.append(segment)
    return merged
