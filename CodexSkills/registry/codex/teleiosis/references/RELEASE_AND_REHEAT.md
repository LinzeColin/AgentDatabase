# Release and Reheat

## Release evidence

A release binds version/revision, Genesis hash, source tree, manifest, archive hash, build environment, full-regression evidence, install transaction, validity and unknowns in external receipts. ZIP creation is deterministic, safely re-extracted and strictly revalidated.

Verification is layered:

- `structural`: no target execution; safe shape, manifest and package checks;
- `release`: non-recursive fast checks for package/install boundaries; the package path also runs the full suite exactly once when not already inside a suite;
- `deep`: explicit full pre-switch requalification, never implicit recursion.

Installation is locked, transactional and observable. The input archive is first frozen to a private, size-bounded snapshot and its source stability is checked before extraction. Internal lock and transaction controls reject links. Every switch has a durable transaction ID and receipt, optional external result file, `install-status`, safe recovery and a content-bound rollback point. The predecessor hash is recorded before rename, allowing the narrow pre-receipt crash window to recover without guessing. Caller interruption cannot be interpreted as success or failure without receipt reconciliation.

The Skill version is not a Genesis constant. This delivery remains `v0.0.0.1` because the user specified it; later user-authorized releases may change versions without modifying Genesis.

## Reheat

Each run is finite. A later improvement uses a new run ID and freezes the prior release. Triggers include evidence expiry, real failure clusters, a materially stronger peer, model/runtime/standard change, dependency deprecation, security event, cost or latency regression, trigger drift, counterfactual probe failure, cross-model transfer loss or Genesis amendment.

`SATURATED` means no credible improvement was found under the current evidence and budget. It never means permanently perfect.
