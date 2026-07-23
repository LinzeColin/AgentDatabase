# Lifecycle, corrections and memory

Release and snapshot boundaries:

- Builder release `v0.0.0.4`.
- Internal target-model semantic snapshots, changed only after evidence/eval promotion.
- Published person-Skill product version `0.0.0.1` through `0.0.0.999`, allocated independently per canonical person and consumed only by successful registration.
- Runtime invocations are unversioned.

Memory layers:

- semantic model: facts/cognition/decision/strategy/persona;
- procedural: verified reusable task routines;
- episodic: run summaries and outcomes;
- user overlay: explicit stable preferences, separated from target identity;
- correction ledger: append-only accepted/rejected/superseded events;
- promotion queue: candidate lessons awaiting evidence and regression tests.

Update rule: snapshot → append new source/correction → impact graph → minimal patch → targeted and global regression → Architect proposal → Skeptic challenge → promote or rollback. One-off convenience must not become a global character rule.

Repeated distillation of the same person may produce multiple published products even when the internal semantic snapshot label is unchanged. Registration order, not invocation count, determines `product_version`.
