from typing import Any
# pyrefly: ignore [missing-import]
import speechbrain.utils.importutils
# pyrefly: ignore [missing-import]
from pyannote.audio import Pipeline
def _patch_speechbrain_windows_compat() -> None:
    try:
        orig_getattr = speechbrain.utils.importutils.LazyModule.__getattr__

        def safe_getattr(self: Any, attr: str) -> Any:
            try:
                return orig_getattr(self, attr)
            except Exception as e:
                raise AttributeError(attr) from e

        speechbrain.utils.importutils.LazyModule.__getattr__ = safe_getattr
    except Exception:
        pass


def diarize_audio(
    audio_path: str,
    model_name: str,
    huggingface_token: str,
) -> list[dict[str, Any]]:
    _patch_speechbrain_windows_compat()
    pipeline = Pipeline.from_pretrained(model_name, use_auth_token=huggingface_token)
    diarization = pipeline(audio_path)
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({"start": float(turn.start), "end": float(turn.end), "speaker": speaker})
    return segments
