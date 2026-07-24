---
doc_id: "P01-PRD"
doc_type: "product_requirements"
version: "0.0.0.1"
status: "frozen_for_acceptance"
---

# PRD｜Dynamic Personal Profile Update Skill

## Customer and problem

The customer is Linze, using ChatGPT/Codex/Memory Atlas across long time spans. Current Custom Instructions and agent memory are limited snapshots. The problem is not merely storing more history; it is detecting meaningful changes in how the user works and turning those changes into an immediately usable, temporary agent action or reusable asset candidate.

## Product outcome

Every meaningful change in the allowlisted derived data can be represented in one compact Profile Delta Markdown file with:

- machine-readable structured facts;
- human-readable explanation;
- evidence and counterevidence;
- time windows, confidence, and expiry boundary;
- a temporary next-agent action;
- Prompt/Workflow/Skill candidates from recurring behavior.

## In scope

- deterministic derived-only extraction;
- content-hash material-change detection;
- one-file dual-plane Markdown output;
- every-three-calendar-days GitHub Action;
- no-change early exit and no empty commit;
- fail-closed validation and atomic replacement;
- Skill registry record, evaluation record, patch-only controlled iteration record;
- Profile-to-Agent-Action Prompt;
- Recurring Asset Miner with one-trial promotion gate.

## Out of scope

- raw transcript ingestion;
- automatic ChatGPT/Codex login, scraping, export download, or memory writeback;
- LLM/API calls in the scheduled processor;
- vector database, graph database, PostgreSQL, embeddings, search index, or second state store;
- overwriting stable profile or Custom Instructions;
- automatic publication of a Skill/Workflow/Prompt;
- public exposure of raw/private personal data;
- the rejected opportunity pool.

## Baseline, targets, and observation period

| Metric | Baseline | v0.0.0.1 target | Measurement |
|---|---|---|---|
| Human + machine readability | Separate agent-specific views | One self-contained Markdown with both planes | Validator + human inspection |
| Persistent profile outputs per run | Not fixed | Exactly one allowed path | Git diff allowlist |
| Same-input repeat behavior | Unknown | `NO_CHANGE`, byte-identical output | Two consecutive deterministic runs |
| Stable-memory pollution | Must be zero | Zero writes outside output | Diff and path audit |
| Raw/private leakage | Must be zero | Zero forbidden paths/content | Validator and credential scan |
| Direct usefulness | Not measured | At least one trial-ready action or asset when evidence supports it | One real task trial |
| Runtime cost | Not measured | No LLM/API; short runner job; no commit on no-change | Action run and diff review |

Observation period: first 3 scheduled checks plus one manual real-task trial. Kill the implementation if it produces only longer reports without reducing clarification, rework, or asset extraction effort.

## Value hypothesis

The value comes from reducing repeated context reconstruction and converting repeated behavior into reusable assets. The cost is acceptable only while deterministic processing, maintenance, and one human review are lower than the saved work. No monetary ROI is promised before the trial evidence exists.
