# White-Box Evidence Contract

White-box means externally auditable facts, not disclosure of private chain-of-thought.

Minimum fields for target and optimizer runs:

```text
run_id
baseline_id + locked Genesis hash
stable version + tree hash
candidate IDs + strategy + tree hashes
valid_as_of + freshness sources + unknowns
scope + non-goals + user hard requirements
authority + budgets + environment
premise decision + research seal + competitor dataset hash
hypothesis + exact diff + changed files + commands + tools + actor
eval contract hash + raw result hashes + process traces
KEEP | REVERT | NO_CHANGE
failed candidates + rejected changes + rollback pointers
2x6 reviewer identities + independent verifier
stop reason + residual risks + reheat triggers
final artifact hash + external release receipt
```

## Change sets

A change set may contain several files when architectural coherence requires it. Every operation is still explicit: add, replace, delete or move; before/after tree hashes; rationale; measured result; decision and rollback snapshot.

## History

Events are hash chained to expose accidental or opportunistic rewriting. This is tamper evidence, not a cryptographic identity signature. Registry-held Genesis and release hashes remain the external anchors.

## Failures

Rejected candidates and `NO_CHANGE` are evidence. They remain outside the installed package in the run log; they are not silently deleted to improve the apparent success rate.

## Seal verification

A seal is not trusted merely because its own JSON digest is internally consistent. Gate-time verification reopens each listed file, recomputes size and SHA-256, detects missing or newly added research evidence, and binds competitor dataset, selection and manifest before the first Candidate mutation.
