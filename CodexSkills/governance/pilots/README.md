# Three representative Skill pilots

Status:
`DRAFT_NON_ACTIVE_THREE_REPRESENTATIVE_PILOTS_SHADOW_COMPLETE_PRODUCTION_BLOCKED`

This directory implements the Mechanism-owned M-068 pilot evidence boundary.
It projects three deterministic, metadata-only Shadow pilots from immutable
public-safe Registry and Mechanism evidence:

- `skill-github-sync`: deterministic sync and three-cycle idempotency;
- `agent-reach`: same-name AGENTS/CODEX identity separation with mandatory
  owner review and no automatic merge;
- `km-bid-evolve`: high-risk iterative evidence bound to the M-046 confirmed
  regression fixture, isolated holdout boundary, and no autonomous promotion.

Every pilot has three byte-stable Shadow cycles. Each cycle closes all
critical gates, carries a synthetic pre-write rollback drill with the five
M-057 verification kinds, and records zero Skill execution, Registry/state
write, notification, or publication side effects. Caller-supplied gate,
status, or summary fields are rejected by exact recomputation.

This is not production pilot evidence. The immutable Registry snapshot has 89
quarantined/unverified Versions and zero binding-eligible Versions. M-057 has
no real champion, M-065 remains blocked in Shadow-only mode, no real
EvalProfile exists for the high-risk pilot, and no provider notification was
sent. Consequently `production_pilots_ready` and the production done gate
remain false.

Rebuild and verify from the repository root:

```bash
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_representative_pilots.py --check
/usr/bin/python3 -B -m unittest \
  CodexSkills.governance.tests.test_representative_pilots
```

The harness has no filesystem, Git, network, source-content, sealed-holdout,
state, publisher, notification, activation, or migration capability. It does
not change the 31-schema/5-policy candidate, Auto plane, OpenAIDatabase,
Registry, source roots, state, watermarks, or `CodexSkills/VERSION`.
