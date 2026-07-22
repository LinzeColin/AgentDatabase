# R8 Formula, Payroll and Policy Input Contract

This is the development-only R8 contract for product `0.2.0-dev.8`. R8 validates governed inputs and deterministic calculations. Every R8 object remains `NOT_EVALUATED_R8`; named-Metric inclusion and final-file generation begin in R9 only.

## Run-first sufficiency and user choices

Every real run must execute the existing R3 input-sufficiency gate and the R8 formula-readiness gate before reading financial source bodies or calculating an in-scope component. A missing or conflicting formula, rate, component registry, payroll control, approved-time source, tax treatment, interest calendar, identity, WBS, evidence binding, or policy binding produces `BLOCKED` and a diagnostic output locator.

The operator must receive the exact missing requirement and these structured choices:

1. supply the required input;
2. provide qualified alternate evidence with an input-resolution record;
3. reduce scope or remove the affected Metric, with the impact stated;
4. explicitly keep the run blocked.

Silence is not permission. Optional presentation may be omitted explicitly, but a generic instruction to omit cannot waive payroll or another non-waivable input while retaining an affected full-cost Metric. Every resolution binds the request, input/config evidence, affected scope and resulting Metric effect. No resolution contains an internal approver field.

Every run must publish or return the absolute output directory plus `output_index.json` and `OUTPUT_INDEX.md`. When blocked, those locators point to diagnostics and review tasks; when all later gates pass, they point to the generated final file and internal-process handoff.

## Formula and rate registry

`src/project_cost_table/formulas.py` accepts only registered expression IDs. It does not use `eval`, floats, free-text expressions, historical backsolves or defaults. An active profile binds:

- formula ID, version, units and allowlisted expression;
- exact scope and inclusive effective dates;
- explicit rounding layer and `ROUND_HALF_UP`;
- request, input and config SHA256 values;
- evidence and, when applicable, company-policy or input-resolution references;
- at least one executable test vector;
- append-only supersession lineage.

Overlapping active formula scopes stop the run. Unknown, template, reference-observed, superseded and deferred profiles cannot calculate or enter a Metric. The historical management-rate observation remains `REFERENCE_OBSERVED_NOT_ACTIVE`; it is not a default. Product 0.2 is CNY-only and actively blocks FX conversion while retaining an explicit deferred registry state.

## Fully loaded payroll

When payroll is in scope, `FULLY_LOADED_EMPLOYER_COST_WITH_APPROVED_TIME` is non-waivable. The effective component registry must classify every observed component as included employer cost, excluded from employer cost, or external labor that cannot enter employee payroll. Missing component treatment is not zero.

The requested payroll-dependent Metric ID is explicit and must match the effective formula scope; it is never hard-coded or inferred. For each legal entity, opaque employee ID and payroll period, R8 enforces:

```text
sum(all source payroll records) = payroll control total
sum(project time + explicit unallocated time) = approved-time control
sum(project allocations) + unallocated payroll pool = allocable employer cost
```

Corrections, reversals and retroactive records retain append-only lineage. Reversals exactly negate their target. Cross-entity allocation, missing project/WBS identity, external-labor ambiguity, guessed day rates and automatic residual spreading block. A rounding remainder stays visible in the unallocated pool; if independently rounded project lines would exceed allocable cost, the run blocks with a signed diagnostic residual instead of silently redistributing one cent.

## Management, tax and interest

- Management cost uses an active, evidence-backed policy profile defining base, rate, scope, period, exceptions and rounding. The historical observed rate cannot activate it.
- Project tax follows direct project evidence, governed project tax ledger, then evidence-backed project allocation policy. Company tax returns are not a default project allocation source. Gross, base, source tax, recomputed tax, rate, invoice type, recoverability and both arithmetic deltas remain visible; source values are never overwritten.
- Interest requires opening principal, dated receipt/payment/prepayment movements, explicit same-day ordering, effective annual rate, start/end dates, an explicit `ACTUAL_365` or `ACTUAL_360` convention matching the profile denominator, rounding layer, evidence and policy. Days are actual calendar days, the start is inclusive, the end is exclusive, and a movement changes principal at the start of its date. Missing inputs or a negative principal state block.

## Manual adjustments

Each adjustment has an explicit signed amount, reason, evidence, formula profile, policy or qualified input resolution, effective period, expiry, reversal policy, request/input/config hashes and supersession or reversal lineage. Expired active adjustments block. Reversals exactly negate the target. No automatic reversal, hidden expiry or cross-scope supersession is allowed.

## Authority boundary and next phase

The Skill does not appoint an internal financial role, represent company authorization, or manage the company approval workflow. After R9 and all later validation gates mark every requested in-scope Metric `VALIDATED`, the Skill generates the final version directly and returns its absolute location. The operator then routes that file through the existing company process outside this Skill.
