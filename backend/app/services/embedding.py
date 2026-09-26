import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

_model_instance = None


def get_embedding_model():
    global _model_instance
    if _model_instance is None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading SentenceTransformer model: {settings.EMBEDDING_MODEL}")
        _model_instance = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model_instance


def get_embedding_dimension() -> int:
    model = get_embedding_model()
    dim = model.get_sentence_embedding_dimension()
    return int(dim) if dim is not None else 384


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    vector = model.encode(text, convert_to_numpy=True)
    return vector.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = get_embedding_model()
    vectors = model.encode(texts, convert_to_numpy=True, batch_size=32)
    return [v.tolist() for v in vectors]
