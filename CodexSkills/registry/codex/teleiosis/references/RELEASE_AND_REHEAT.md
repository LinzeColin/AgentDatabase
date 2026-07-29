# Release and Reheat

## Release evidence

A release binds version/revision, Genesis hash, source tree, manifest, archive hash, build environment, full-regression evidence, install transaction, validity and unknowns in external receipts. ZIP creation is deterministic, safely re-extracted and strictly revalidated.

Verification is layered:

- `structural`: no target execution; safe shape, manifest and package checks;
- `release`: non-recursive fast checks for package/install boundaries; the package path runs the full suite once when not already nested;
- `deep`: explicit full pre-switch requalification, never implicit recursion.

Installation is locked, transactional and observable. The input archive is frozen to a private size-bounded snapshot before extraction. Every switch has a durable transaction ID, optional external result file, committed-state verification, recovery and a content-bound rollback point.

The Skill version is not a Genesis constant. This Candidate is `v0.0.0.2`; the locked Genesis remains v0.0.0.1 and byte-identical. Implementation versions may advance when WBI-GB-001—027 are not weakened.

## Non-negative release rule

Before selecting a Candidate, `utility-gate` requires at least one material measured gain and no protected or hard regression. Otherwise it chooses `KEEP_BASELINE` or `REVERT`. Packaging success cannot compensate an outcome, security, provenance or protected-task failure.

## Reheat

Each run is finite. A later improvement uses a new run ID and freezes the prior release. Triggers include evidence expiry, real failure clusters, a materially stronger peer, model/runtime/standard change, dependency deprecation, security event, cost/latency/operator regression, trigger drift, counterfactual probe failure, cross-model transfer loss or Genesis amendment.

`SATURATED` means no credible improvement was found under the current evidence and budget. It never means permanently perfect.
