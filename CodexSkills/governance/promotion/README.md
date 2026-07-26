# Promotion controller

This directory materializes the Mechanism-owned, non-active implementation of
Task Pack `M-056`.

`controller.py` is a pure append-only `PROMOTE` / `REJECT` controller. It
requires a trusted contract bundle, an externally pinned Registry snapshot,
content-addressed eval runs and scorecards, a promotion evidence bundle, and a
promotion decision. It validates the complete reference closure before
returning canonical decision bytes and an immutable replay view.
Every authorized append also requires an externally pinned predecessor-ledger
digest. The ledger digest binds the exact Registry snapshot and the ordered
decision-digest history, so a caller cannot silently truncate or replace prior
events.

Because lifecycle status has no `REJECTED` value, a reject event is represented
as `stage=REJECTED` with the candidate transition
`CHALLENGER -> QUARANTINED`; the current champion remains unchanged.

The controller does not persist a ledger, mutate Registry records, write Git
or `CodexSkills/VERSION`, send notifications, activate a bundle, or publish
artifacts. The real Registry currently has no `CHALLENGER` or `CHAMPION`
version, so real promotion execution remains forbidden.

`ROLLBACK` and `REVOKE` are deliberately rejected with
`PROMOTION_ROLLBACK_REVOCATION_PHASE_REQUIRED`; those semantics belong to the
next independent Task Pack phase, `M-057`.
