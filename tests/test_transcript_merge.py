from app.services.merge import merge_transcript


def test_merge_uses_word_timestamp_speaker_boundaries():
    transcription = [
        {
            "start": 0.0,
            "end": 4.0,
            "text": "Hello budget",
            "words": [
                {"start": 0.0, "end": 1.0, "word": "Hello"},
                {"start": 2.1, "end": 4.0, "word": "budget"},
            ],
        }
    ]
    diarization = [
        {"start": 0.0, "end": 2.0, "speaker": "SPEAKER_A"},
        {"start": 2.0, "end": 5.0, "speaker": "SPEAKER_B"},
    ]

    assert merge_transcript(transcription, diarization) == [
        {"speaker": "Speaker 1", "start": 0.0, "end": 1.0, "text": "Hello"},
        {"speaker": "Speaker 2", "start": 2.1, "end": 4.0, "text": "budget"},
    ]


def test_merge_falls_back_to_transcription_segments():
    transcription = [{"start": 1.0, "end": 3.0, "text": "Good morning"}]
    diarization = [{"start": 0.0, "end": 4.0, "speaker": "SPEAKER_A"}]

    assert merge_transcript(transcription, diarization) == [
        {"speaker": "Speaker 1", "start": 1.0, "end": 3.0, "text": "Good morning"}
    ]