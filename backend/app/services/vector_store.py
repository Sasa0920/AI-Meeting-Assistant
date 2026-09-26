import logging
import uuid
from typing import Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models
from app.config import settings
from app.services.embedding import get_embedding_dimension

logger = logging.getLogger(__name__)

_client_instance: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    global _client_instance
    if _client_instance is not None:
        return _client_instance

    if settings.QDRANT_PATH:
        logger.info(f"Connecting to local Qdrant at path: {settings.QDRANT_PATH}")
        _client_instance = QdrantClient(path=settings.QDRANT_PATH)
        return _client_instance

    try:
        logger.info(f"Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=3.0)
        # Test connection
        client.get_collections()
        _client_instance = client
        return _client_instance
    except Exception as e:
        logger.warning(
            f"Could not connect to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT} ({e}). "
            f"Falling back to in-memory Qdrant client."
        )
        _client_instance = QdrantClient(":memory:")
        return _client_instance


def set_qdrant_client(client: QdrantClient):
    """Allows test fixtures to inject custom or in-memory clients."""
    global _client_instance
    _client_instance = client


def ensure_collection(collection_name: Optional[str] = None):
    name = collection_name or settings.QDRANT_COLLECTION
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    if name not in collections:
        dim = get_embedding_dimension()
        logger.info(f"Creating Qdrant collection '{name}' with dimension {dim} and Cosine distance.")
        client.create_collection(
            collection_name=name,
            vectors_config=rest_models.VectorParams(
                size=dim,
                distance=rest_models.Distance.COSINE,
            ),
        )


def delete_meeting_points(meeting_id: str, collection_name: Optional[str] = None):
    name = collection_name or settings.QDRANT_COLLECTION
    client = get_qdrant_client()
    ensure_collection(name)
    client.delete(
        collection_name=name,
        points_selector=rest_models.FilterSelector(
            filter=rest_models.Filter(
                must=[
                    rest_models.FieldCondition(
                        key="meeting_id",
                        match=rest_models.MatchValue(value=meeting_id),
                    )
                ]
            )
        ),
    )


def insert_chunks(
    chunks: list[dict[str, Any]],
    vectors: list[list[float]],
    collection_name: Optional[str] = None,
) -> int:
    if not chunks or not vectors or len(chunks) != len(vectors):
        return 0

    name = collection_name or settings.QDRANT_COLLECTION
    client = get_qdrant_client()
    ensure_collection(name)

    points = []
    for chunk, vector in zip(chunks, vectors):
        point_id = str(uuid.uuid4())
        points.append(
            rest_models.PointStruct(
                id=point_id,
                vector=vector,
                payload=chunk,
            )
        )

    # Upsert in batches of 64
    batch_size = 64
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=name, points=batch)

    return len(points)


def search_similar_chunks(
    query_vector: list[float],
    meeting_id: Optional[str] = None,
    limit: int = 5,
    collection_name: Optional[str] = None,
) -> list[dict[str, Any]]:
    name = collection_name or settings.QDRANT_COLLECTION
    client = get_qdrant_client()
    ensure_collection(name)

    query_filter = None
    if meeting_id:
        query_filter = rest_models.Filter(
            must=[
                rest_models.FieldCondition(
                    key="meeting_id",
                    match=rest_models.MatchValue(value=meeting_id),
                )
            ]
        )

    # Use client.query_points or client.search
    search_results = client.search(
        collection_name=name,
        query_vector=query_vector,
        query_filter=query_filter,
        limit=limit,
    )

    results = []
    for scored_point in search_results:
        payload = scored_point.payload or {}
        results.append({
            **payload,
            "score": round(float(scored_point.score), 4),
        })

    return results
