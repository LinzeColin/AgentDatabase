# AU-040 transport schema draft

State: `DRAFT_NON_ACTIVE`.

This directory isolates four Auto-owned public schema proposals while the
current trusted candidate remains exactly 29 schemas and five policies:

- `daily-run-shard-manifest:v1`
- `run-event-index-entry:v1`
- `publication-manifest:v2`
- `retention-receipt:v3`

The draft composes 31 schemas with the current five policies for offline
schema validation only. The target `retention-policy:v3` is not present; it
must later replace v2 after independent Mechanism acceptance. This directory
is not an active or candidate bundle, is not consumed by the runtime publisher,
writer, queue, retention executor, or OpenAIDatabase consumer, and does not
permit a repository shard.

Run the deterministic draft gates from the repository root:

```bash
/usr/bin/python3 -B \
  CodexSkills/registry/auto/tools/build_transport_draft.py --check
/usr/bin/python3 -B \
  CodexSkills/registry/auto/tools/validate_transport_draft.py lint-draft
/usr/bin/python3 -B -m unittest \
  discover -s CodexSkills/registry/auto/tests -p 'test_transport_draft.py'
```

The semantic validator checks per-line JCS/LF framing, manifest arithmetic and
Sydney dates, persistent index closure, exact correction targets, operation /
path / serialization routing, active-tree prune evidence, and strict retention
time boundaries. Active-tree receipts derive a per-item 24-hour deadline and
must truthfully record any late-prune breach; equality with the deadline is
still on time. The validator runs the current Mechanism public-value scanner
against all legal fixtures. The exact blocked digest-field names are emitted in
`draft-interface.json`; the repository policy is not changed or bypassed.

## Path promotion guard

`transport-draft/` is an isolation path only. A candidate manifest must never
name a path containing `draft`. Each interface entry binds its current draft
path and one future canonical path under the sibling root
`CodexSkills/registry/auto/schemas/public-v2/`.

The sibling root is intentional. The current candidate loader recursively
enumerates `CodexSkills/registry/auto/schemas/public/` and requires the exact
existing schema set. Placing future schemas below that root would contaminate
the trusted 29-schema candidate before promotion.

The ownership-safe sequence is fixed:

1. Auto transport schema draft.
2. Mechanism semantic/policy acceptance without bundle materialization.
3. Auto promotion of the accepted exact bytes to `schemas/public-v2/`.
4. Mechanism final 31/5 candidate, consumer, and control materialization.
5. Auto integration against the exact new bundle.

Until all five stages complete, `repository_bound=false`, AU-040 remains false,
and activation and canonical publication remain forbidden.
