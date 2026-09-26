# pyrefly: ignore [missing-import]
import pytest
from qdrant_client import QdrantClient

from app.services.vector_store import (
    delete_meeting_points,
    ensure_collection,
    insert_chunks,
    search_similar_chunks,
    set_qdrant_client,
)


@pytest.fixture(autouse=True)
def memory_qdrant():
    client = QdrantClient(":memory:")
    set_qdrant_client(client)
    ensure_collection("test_knowledge")
    return client


def test_insert_and_search_chunks():
    chunks = [
        {
            "meeting_id": "m-1",
            "filename": "meeting1.mp3",
            "speaker": "Speaker 1",
            "start_time": 0.0,
            "end_time": 10.0,
            "source_type": "transcript",
            "text": "Discussion on database indexes",
        },
        {
            "meeting_id": "m-2",
            "filename": "meeting2.mp3",
            "speaker": "Speaker 2",
            "start_time": 0.0,
            "end_time": 15.0,
            "source_type": "transcript",
            "text": "Discussion on marketing campaign",
        },
    ]

    # Create 384-dimensional dummy vectors
    vec1 = [0.1] * 384
    vec2 = [-0.1] * 384
    vectors = [vec1, vec2]

    inserted = insert_chunks(chunks, vectors, collection_name="test_knowledge")
    assert inserted == 2

    # Query with vec1
    results = search_similar_chunks(vec1, limit=2, collection_name="test_knowledge")
    assert len(results) == 2
    assert results[0]["meeting_id"] == "m-1"
    assert "database indexes" in results[0]["text"]


def test_filtered_search_by_meeting_id():
    chunks = [
        {"meeting_id": "m-1", "filename": "m1.mp3", "text": "Auth PR details", "source_type": "transcript"},
        {"meeting_id": "m-2", "filename": "m2.mp3", "text": "Another auth detail", "source_type": "transcript"},
    ]
    vectors = [[0.2] * 384, [0.2] * 384]
    insert_chunks(chunks, vectors, collection_name="test_knowledge")

    results = search_similar_chunks(
        [0.2] * 384,
        meeting_id="m-1",
        limit=5,
        collection_name="test_knowledge",
    )
    assert len(results) == 1
    assert results[0]["meeting_id"] == "m-1"


def test_delete_meeting_points():
    chunks = [
        {"meeting_id": "m-1", "filename": "m1.mp3", "text": "Old details", "source_type": "transcript"},
    ]
    vectors = [[0.3] * 384]
    insert_chunks(chunks, vectors, collection_name="test_knowledge")

    delete_meeting_points("m-1", collection_name="test_knowledge")
    results = search_similar_chunks([0.3] * 384, limit=5, collection_name="test_knowledge")
    assert len(results) == 0
