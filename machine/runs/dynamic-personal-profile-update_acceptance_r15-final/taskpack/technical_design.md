---
doc_id: "P01-ARCHITECTURE"
doc_type: "architecture"
version: "0.0.0.1"
status: "frozen_for_acceptance"
---

# Architecture

## Repository topology

```text
AgentDatabase/
├── CodexSkills/
│   ├── registry/
│   │   ├── agents/
│   │   ├── claude/
│   │   ├── codex-system/
│   │   └── codex/
│   │       └── dynamic-personal-profile-update/
│   ├── skill_log_evals/
│   └── skill_controlled_iterate/
├── OpenAIDatabase/
│   ├── data/derived/profile/DYNAMIC_PROFILE.md
│   └── data/run_logs/skills_runs/
└── .github/workflows/dynamic-profile-update.yml
```

The registry now contains the P-01 `codex` registration. The four existing
mirror namespaces remain untouched until the separately gated `T02` migration;
that migration must update `sync_skills.py` and root compatibility indexes in
one tested change. This package does not claim that broad migration is already
complete.

## Runtime flow

```text
allowlisted derived files
        ↓
deterministic parser
        ↓
canonical source snapshot + normalized signals
        ↓
material-change gate
        ├── no change → NO_CHANGE, no write, no commit
        └── change → atomic write of DYNAMIC_PROFILE.md
                         ↓
                    fail-closed validator
                         ↓
                    commit only that file
```

## Source boundary

v0.0.0.1 reads only the explicit allowlist in `skill/scripts/update_dynamic_profile.py`. The processor must not recursively scan the repository and must not infer permission from a path that merely contains the word `derived`.

## Single-file dual plane

- Machine plane: YAML front matter with stable IDs, hashes, source paths, time windows, status, confidence, evidence, counterevidence, action, and asset classification.
- Human plane: concise conclusions, changes, immediate agent action, recurring candidates, and uncertainty.
- Both planes are rendered from one in-memory representation in one process. No human-maintained duplicate is allowed.

## Separation of concerns

- Skill: tells Codex how and when to use the capability.
- Script: deterministic implementation.
- Workflow: schedule, permissions, checkout, validation, and commit gate.
- Registry: five-layer identity/provenance/capability/verification/control record.
- Evaluation: proof that the Skill works.
- Controlled iteration: patch-only change policy and rollback.
- Run log: compact runtime facts only; not a second profile store.

## Discovery route

The static Memory Atlas route `dynamic_profile` points agents to
`data/derived/profile/DYNAMIC_PROFILE.md` as a read-only generated view. It is
not part of the canonical stable profile and is loaded only when the task needs
time-aware profile deltas or trial-ready asset candidates. Route wiring changes
are configuration changes, not scheduled profile output; the scheduled Action
still has exactly one persistent output file.
