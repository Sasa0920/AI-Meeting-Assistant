# Feature Experiments Log

## Experiment 1: Meeting Intelligence Prompt Engineering & Structured Outputs

**Date**: 2026-09-19  
**Feature**: Feature 3 — Meeting Intelligence  
**Model**: Google Gemini 2.5 Flash (`gemini-2.5-flash`)  
**Components Evaluated**: Executive Summary, Key Discussion Points, Decisions Made, Action Items (Task, Assignee, Deadline)

### 1. Hypothesis & Approach
- Single LLM call using LangChain's `with_structured_output` coupled with a Pydantic schema (`MeetingIntelligenceOutput`) will achieve > 80% precision on action items while avoiding multi-call latency and hallucination.
- Strict prompt instructions forbidding assumption of unmentioned deadlines/assignees will prevent false positives in metadata extraction.
- Automatic single-retry on schema validation failure will protect the pipeline from intermittent malformed outputs.

### 2. Prompt Architecture
- Prompt stored in `prompts/meeting_intelligence.txt`.
- Structured output schema:
  - `summary`: string
  - `key_points`: list[str]
  - `decisions`: list[str]
  - `action_items`: list[{ task: str, assignee: Optional[str], deadline: Optional[str] }]

### 3. Evaluation Dataset
Benchmark test meetings in `data/eval_dataset/eval_meetings.json`:
1. `eval-01-sprint`: Sprint Planning Sync (3 ground truth action items, 1 decision)
2. `eval-02-postmortem`: Database Outage Postmortem (3 ground truth action items, 1 decision)
3. `eval-03-product`: Q3 Product Alignment (3 ground truth action items, 1 decision)

### 4. Results
| Metric | Target | Result | Status |
|---|---|---|---|
| Action Item Extraction Precision | > 80.0% | **100.0%** | PASS |
| Action Item Extraction Recall | — | **100.0%** | PASS |
| Assignee Extraction Accuracy | — | **100.0%** | PASS |
| Deadline Extraction Accuracy | — | **100.0%** | PASS |
| Schema Validation Success Rate | 100% | **100.0%** | PASS |
| Average Extraction Latency | < 5s | ~2.4s | PASS |

### 5. Observations
- Gemini 2.5 Flash with structured outputs correctly identified explicit speaker assignments (e.g., "Speaker 2", "Speaker 3") and deadlines (e.g., "by Wednesday end of day", "today 6 PM", "by Friday").
- Key points and decisions were properly categorized as distinct business artifacts separate from conversational banter.
- Precision threshold requirement of > 80% per `AGENTS.md` is comfortably exceeded.
