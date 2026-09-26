"""Knowledge Base & RAG Evaluation Benchmark Script.

Evaluates:
- Retrieval Recall@K (Target > 85%)
- Answer Correctness on Ground Truth Questions (Target > 85%)
- Hallucination Prevention on Negative Controls (Target 100%)
"""

import json
import os
import sys
import time

# Add backend to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(PROJECT_ROOT, "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from qdrant_client import QdrantClient
from app.services.vector_store import (
    set_qdrant_client,
    ensure_collection,
    insert_chunks,
)
from app.services.chunking import chunk_meeting
from app.services.embedding import embed_batch
from app.services.rag import answer_meeting_query


def setup_evaluation_knowledge_base():
    """Populates an in-memory vector store with benchmark meetings."""
    eval_client = QdrantClient(":memory:")
    set_qdrant_client(eval_client)
    ensure_collection()

    eval_meetings_file = os.path.join(PROJECT_ROOT, "data", "eval_dataset", "eval_meetings.json")
    with open(eval_meetings_file, "r", encoding="utf-8") as f:
        meetings = json.load(f)

    total_chunks = 0
    print(f"Indexing {len(meetings)} benchmark meetings into test vector store...")

    for m in meetings:
        meeting_id = m["id"]
        filename = f"{m['name']}.mp3"
        segments = m["transcript"]
        ground_truth = m.get("ground_truth", {})

        intel = {
            "summary": f"Discussion about {m['name']}",
            "decisions": ground_truth.get("decisions", []),
            "action_items": ground_truth.get("action_items", []),
        }

        chunks = chunk_meeting(
            meeting_id=meeting_id,
            filename=filename,
            segments=segments,
            intelligence=intel,
        )

        texts = [c["text"] for c in chunks]
        vectors = embed_batch(texts)
        count = insert_chunks(chunks, vectors)
        total_chunks += count
        print(f"  Indexed '{meeting_id}': {count} chunks")

    print(f"Total indexed chunks: {total_chunks}\n")
    return eval_client


def run_rag_evaluation():
    setup_evaluation_knowledge_base()

    questions_file = os.path.join(PROJECT_ROOT, "data", "eval_dataset", "eval_rag_questions.json")
    with open(questions_file, "r", encoding="utf-8") as f:
        test_questions = json.load(f)

    print("=" * 75)
    print("AI Meeting Assistant — Feature 4 RAG & Knowledge Base Evaluation")
    print("=" * 75)

    answerable_count = 0
    retrieval_hits = 0
    answer_correct_hits = 0

    unanswerable_count = 0
    negative_pass_count = 0

    for idx, tq in enumerate(test_questions, start=1):
        q_id = tq["id"]
        question = tq["question"]
        is_answerable = tq["is_answerable"]
        target_meeting = tq.get("target_meeting_id")
        keywords = tq.get("expected_answer_keywords", [])

        print(f"[{idx}/{len(test_questions)}] Query: \"{question}\"")
        result = answer_meeting_query(question, top_k=4)

        if is_answerable:
            answerable_count += 1
            # Check retrieval hit
            cited_meeting_ids = {s.meeting_id for s in result.sources}
            retrieval_hit = target_meeting in cited_meeting_ids
            if retrieval_hit:
                retrieval_hits += 1

            # Check keyword presence in answer
            answer_lower = result.answer.lower()
            matched_kw = [kw for kw in keywords if kw.lower() in answer_lower]
            answer_correct = (len(matched_kw) >= max(1, len(keywords) // 2)) and not result.insufficient_evidence
            if answer_correct:
                answer_correct_hits += 1

            status_str = "PASS" if (retrieval_hit and answer_correct) else "FAIL"
            print(f"  Status: {status_str} | Retrieval Hit: {retrieval_hit} | Keywords Matched: {len(matched_kw)}/{len(keywords)}")
            print(f"  Answer: {result.answer[:120]}...")
        else:
            unanswerable_count += 1
            negative_pass = result.insufficient_evidence
            if negative_pass:
                negative_pass_count += 1

            status_str = "PASS" if negative_pass else "FAIL (Hallucinated)"
            print(f"  Status: {status_str} | Insufficient Evidence Flag: {result.insufficient_evidence}")
            print(f"  Answer: {result.answer[:120]}...")

        print("-" * 75)
        if idx < len(test_questions):
            time.sleep(13)

    retrieval_recall = (retrieval_hits / answerable_count * 100) if answerable_count > 0 else 0.0
    answer_accuracy = (answer_correct_hits / answerable_count * 100) if answerable_count > 0 else 0.0
    negative_accuracy = (negative_pass_count / unanswerable_count * 100) if unanswerable_count > 0 else 0.0

    print("\n" + "=" * 75)
    print("EVALUATION RESULTS SUMMARY")
    print("=" * 75)
    print(f"Answerable Questions Evaluated: {answerable_count}")
    print(f"Retrieval Recall@4:              {retrieval_recall:.1f}% (Target: > 85.0%)")
    print(f"Answer Grounding / Accuracy:    {answer_accuracy:.1f}% (Target: > 85.0%)")
    print(f"Negative Controls Evaluated:     {unanswerable_count}")
    print(f"Hallucination Prevention Rate:  {negative_accuracy:.1f}% (Target: 100.0%)")
    print("=" * 75)

    success = (retrieval_recall >= 85.0) and (answer_accuracy >= 85.0) and (negative_accuracy == 100.0)
    print(f"Final Verdict: {'PASSED' if success else 'FAILED'}")
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = run_rag_evaluation()
    sys.exit(exit_code)
