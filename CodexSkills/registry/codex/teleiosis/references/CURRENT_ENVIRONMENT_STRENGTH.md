# Current-Environment Strength and Evidence Lease

This protocol implements WBI-GB-028 without claiming permanent superiority.

## Two snapshots

A formal run freezes `current_environment_snapshot` twice: before Candidate mutation and before final delivery. Each snapshot binds the exact target and optimizer trees, authorized runtime and tools, current frontier evidence, benchmark, behavior coverage, Skill-library shadowing evidence, unknowns, expiry and event-driven reheat triggers.

## Claim states

- `PARETO_UNDOMINATED_FOR_VERIFIED_CURRENT_ENVIRONMENT`: every required evidence domain passes and no hard-gate-clean Candidate in the frozen feasible set dominates the selected Candidate under the same environment and budget.
- `NOT_PROVEN`: engineering evidence exists but outcome, cost, coverage, shadowing or frontier evidence is incomplete.
- `REGRESSED`: hard regression or dominance is observed.
- `BLOCKED`: identity, evidence or capability prevents a valid comparison.
- `REHEAT_REQUIRED`: evidence lease expired or a material environment event invalidated the claim.

No state means permanent whole-market supremacy. Closed systems and future releases remain explicit unknowns. Use `environment-snapshot` and `environment-attest`; externally anchor both the base Genesis and effective Genesis hashes.
