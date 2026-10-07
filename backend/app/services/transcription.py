from typing import Any


def transcribe_audio(audio_path: str, model_name: str) -> list[dict[str, Any]]:
    # pyrefly: ignore [missing-import]
    import whisper  # lazy import — avoids loading torch/whisper at module level
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path, word_timestamps=True)
    return result.get("segments", [])

