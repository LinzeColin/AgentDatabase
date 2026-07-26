# Promotion controller

This directory materializes the Mechanism-owned, non-active implementations of
Task Pack `M-056` and `M-057`.

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
independent `rollback_controller.py` boundary.

`rollback_controller.py` replays one append-only lifecycle ledger containing
`PROMOTE`, `REJECT`, `ROLLBACK`, and `REVOKE`. Promotion/rejection steps are
delegated to the unchanged M-056 controller using the current derived champion
map. Rollback/revocation steps consume a separately digest-pinned
`rollback-drill-evidence:v1` contract and require:

- the exact Registry snapshot and predecessor lifecycle-ledger digest;
- the current champion and restore target record/model/event closure;
- proof derived from the ordered ledger that the restore target was a prior
  champion in the same Identity scope;
- complete reference, restore-plan, restore-test, state-snapshot, and trigger
  evidence;
- `PRE_WRITE_SENT` for a planned rollback, or containment readback followed by
  `POST_CONTAINMENT_SENT` for an emergency action; and
- a passing restorable-target claim with no history rewrite.

A revoked version can never become a restore target. A rolled-back version is
derived as `DEPRECATED`, while a revoked version is derived as `REVOKED`.
Rollback and revocation decisions are new `promotion-decision:v1` events; no
prior event or Registry record is edited. The controller can validate later
promotion steps against the restored champion without weakening M-056 gates.

The restore-drill and readiness schemas remain bundle-external. Callers must
pin the drill schema's canonical digest explicitly; the repository copy cannot
authorize itself. This Phase still performs no state write, notification,
activation, or canonical publication.
