# Lifecycle, corrections and memory

Three version axes:

- Builder release `v0.0.0.3`.
- Target model semantic version, changed only after evidence/eval promotion.
- Per-invocation artifact `0.0.0.N`, monotonically increasing and never reused.

Memory layers:

- semantic model: facts/cognition/decision/strategy/persona;
- procedural: verified reusable task routines;
- episodic: run summaries and outcomes;
- user overlay: explicit stable preferences, separated from target identity;
- correction ledger: append-only accepted/rejected/superseded events;
- promotion queue: candidate lessons awaiting evidence and regression tests.

Update rule: snapshot → append new source/correction → impact graph → minimal patch → targeted and global regression → Architect proposal → Skeptic challenge → promote or rollback. One-off convenience must not become a global character rule.
