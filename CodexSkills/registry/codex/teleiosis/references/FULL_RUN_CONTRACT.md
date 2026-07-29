# Full Run Contract

## Canonical sequence

A public Teleiosis invocation is exactly three groups, each containing three rounds. Every round executes `T -> C -> S -> C -> P -> C` over one Candidate lineage. There is no task router.

`C` is the actual iteration object after the preceding module. It is represented by a candidate revision record, not by a predeclared hash. Optional fingerprints are computed after the stage and stored only as audit evidence.

## Counts

- groups: 3
- rounds per group: 3
- module stages: 27
- candidate revisions: 27
- T/S/P calls: 9 each

## Candidate revision minimum fields

- candidate_id
- revision_id and revision_number
- parent_revision_id
- module and group/round position
- candidate_path
- result
- changed_files and diff/evidence references
- tests and rollback_pointer
- optional content_fingerprint computed after the operation

## Anti-recursion

T/S/P are internal stages (`internal_stage=true`). They traverse their complete capability manifests but never launch a second public Run.

## Completion

A Run is complete only when all 27 stages occur in order, no capability is silently omitted, every revision has a parent and rollback pointer, and no `NOT_RUN` or `BLOCKED` stage is treated as success.
