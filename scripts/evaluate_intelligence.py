"""Meeting Intelligence Evaluation Benchmark Script.

Evaluates Gemini LLM meeting intelligence extraction against the benchmark
dataset in data/eval_dataset/eval_meetings.json.
Measures:
- Action Item Precision (Target > 80%)
- Action Item Recall
- Assignee Extraction Accuracy
- Deadline Extraction Accuracy
- Decision Extraction
"""

import json
import os
import sys

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(PROJECT_ROOT, "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.services.intelligence import (
    extract_meeting_intelligence,
    format_transcript_for_llm,
)


def fuzzy_match(text_a: str, text_b: str) -> bool:
    """Basic lexical overlap similarity."""
    words_a = set(text_a.lower().replace(",", "").replace(".", "").split())
    words_b = set(text_b.lower().replace(",", "").replace(".", "").split())
    if not words_a or not words_b:
        return False
    intersection = words_a.intersection(words_b)
    # Match if >= 40% of words overlap
    overlap = len(intersection) / min(len(words_a), len(words_b))
    return overlap >= 0.4


def run_evaluation():
    eval_file = os.path.join(PROJECT_ROOT, "data", "eval_dataset", "eval_meetings.json")
    if not os.path.exists(eval_file):
        print(f"Error: Evaluation dataset not found at {eval_file}")
        sys.exit(1)

    with open(eval_file, "r", encoding="utf-8") as f:
        benchmark_meetings = json.load(f)

    total_gt_actions = 0
    total_pred_actions = 0
    true_positives = 0
    assignee_matches = 0
    deadline_matches = 0

    print("=" * 70)
    print("AI Meeting Assistant — Feature 3 Intelligence Evaluation")
    print("=" * 70)

    results = []

    for item in benchmark_meetings:
        m_id = item["id"]
        m_name = item["name"]
        transcript = item["transcript"]
        ground_truth = item["ground_truth"]
        gt_actions = ground_truth["action_items"]
        total_gt_actions += len(gt_actions)

        print(f"\nEvaluating: {m_name} ({m_id})...")
        formatted_transcript = format_transcript_for_llm(transcript)

        try:
            intel = extract_meeting_intelligence(formatted_transcript)
        except Exception as exc:
            print(f"  Extraction failed with error: {exc}")
            continue

        pred_actions = intel.action_items
        total_pred_actions += len(pred_actions)

        # Match predicted actions to ground truth
        matched_gt_indices = set()
        matched_pred_indices = set()

        for p_idx, pred in enumerate(pred_actions):
            for g_idx, gt in enumerate(gt_actions):
                if g_idx in matched_gt_indices:
                    continue
                if fuzzy_match(pred.task, gt["task"]):
                    matched_gt_indices.add(g_idx)
                    matched_pred_indices.add(p_idx)
                    true_positives += 1

                    # Check assignee
                    pred_ass = (pred.assignee or "").strip().lower()
                    gt_ass = (gt.get("assignee") or "").strip().lower()
                    if pred_ass and (pred_ass in gt_ass or gt_ass in pred_ass):
                        assignee_matches += 1

                    # Check deadline
                    pred_dead = (pred.deadline or "").strip().lower()
                    gt_dead = (gt.get("deadline") or "").strip().lower()
                    if pred_dead and (pred_dead in gt_dead or gt_dead in pred_dead or fuzzy_match(pred_dead, gt_dead)):
                        deadline_matches += 1
                    break

        print(f"  Summary: {intel.summary[:80]}...")
        print(f"  Decisions: {len(intel.decisions)} extracted (GT: {len(ground_truth['decisions'])})")
        print(f"  Action items extracted: {len(pred_actions)}, Matched GT: {len(matched_gt_indices)}/{len(gt_actions)}")

        results.append({
            "id": m_id,
            "name": m_name,
            "gt_actions_count": len(gt_actions),
            "pred_actions_count": len(pred_actions),
            "matched": len(matched_gt_indices),
            "summary_length": len(intel.summary),
            "decisions_count": len(intel.decisions),
        })

    precision = (true_positives / total_pred_actions * 100) if total_pred_actions > 0 else 0.0
    recall = (true_positives / total_gt_actions * 100) if total_gt_actions > 0 else 0.0
    assignee_acc = (assignee_matches / true_positives * 100) if true_positives > 0 else 0.0
    deadline_acc = (deadline_matches / true_positives * 100) if true_positives > 0 else 0.0

    print("\n" + "=" * 70)
    print("BENCHMARK EVALUATION RESULTS SUMMARY")
    print("=" * 70)
    print(f"Total Benchmark Meetings:        {len(benchmark_meetings)}")
    print(f"Ground Truth Action Items:       {total_gt_actions}")
    print(f"Predicted Action Items:          {total_pred_actions}")
    print(f"Matched True Positives:          {true_positives}")
    print("-" * 70)
    print(f"Action Item Precision:           {precision:.1f}%  (Target: > 80.0%)")
    print(f"Action Item Recall:              {recall:.1f}%")
    print(f"Assignee Extraction Accuracy:    {assignee_acc:.1f}%")
    print(f"Deadline Extraction Accuracy:    {deadline_acc:.1f}%")
    print("=" * 70)

    if precision >= 80.0:
        print("\nPASSED: Action item extraction precision meets the > 80% requirement!")
        return 0
    else:
        print(f"\nFAILED: Action item precision {precision:.1f}% is below 80.0% requirement.")
        return 1


if __name__ == "__main__":
    sys.exit(run_evaluation())
