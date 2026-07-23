# R7 Dedup, Event Links and Reconciliation Contract

This contract is development-only for product `0.2.0-dev.7`. It defines event-level data controls. It does not decide named Metrics, generate a formal project-cost workbook, appoint a finance owner or authorized person, or manage company approval.

## Entry gate

1. Run the R3 input-sufficiency gate before opening any business source body.
2. Require manifest-selected, digest-locked sources, active private reader policies, R4 identity evidence and the requested as-of scope.
3. If a required identity, version decision, link identifier, allocation rule or evidence item is missing, stop formal processing and present one compact numbered choice matrix: supply evidence, use a qualified alternate, reduce scope, omit optional presentation only, or stop.
4. Silence is never authorization. Non-waivable source, identity, arithmetic, lineage and conservation gates cannot be omitted.
5. On every pass, block or error, report the absolute output directory, primary result and output index in the conversation and machine output.

## Relation-event boundary

`RelationEvent` is an immutable R7 view of an existing economic event. It binds:

- source system, source artifact digest, business key/digest and source-record references;
- direction, lifecycle stage, source status, event date and signed CNY minor-unit amount;
- full canonical project/entity/WBS/contract identity plus R4 record/resolution/evidence; or
- `ALLOCATION_REQUIRED`, which carries only legal entity and evidence, never a partially asserted canonical scope.

The view is tamper-evident and fixed at `NOT_EVALUATED_R7`. It cannot create a financial fact, approve a company transaction or enter a named Metric by itself.

## Same-stage dedup

| Class | Automatic effect | Required handling |
| --- | --- | --- |
| `BYTE_DUPLICATE` | keep one, exclude exact alias | preserve alias lineage |
| `SAME_KEY_SAME_VERSION` | keep one, exclude exact normalized version alias | preserve all event/source refs |
| `SAME_KEY_CHANGED_VERSION` | none | exact event-set version resolution + evidence; otherwise pending |
| `BUSINESS_CONTENT_DUPLICATE` | none across different keys | exact event-set equivalence resolution + evidence; otherwise pending |
| `POSSIBLE_DUPLICATE` | none | stable ID or qualified evidence; similarity remains candidate |
| `DISTINCT` | include at event-control layer | later Metric rules still apply |

Rules:

- Partition by legal entity, canonical project, WBS/cost code, contract, direction and lifecycle stage before candidate comparison.
- Stop before comparison if the total partitioned pair count exceeds `1,000,000`.
- Never deduplicate across lifecycle stages.
- Changed amount, status, date or source digest under the same business key is a version conflict, not a duplicate.
- Amount/date/counterparty/document/text similarity cannot auto-resolve, auto-exclude or auto-link.
- A resolution binds the complete candidate event set, selected canonical event, input-resolution reference and hash evidence. Stale or unused resolutions block.
- Preserve superseded events and exact aliases; do not overwrite history.

## Typed event links

Allowed relations:

- `DERIVED_FROM`
- `FULFILLS_COMMITMENT`
- `ACCRUAL_FOR`
- `REVERSES`
- `SUPERSEDES`
- `INVOICES`
- `POSTS_TO_GL`
- `SETTLES`
- `ALLOCATES_TO`
- `TRANSFERRED_BETWEEN`
- `REFERENCES_ONLY`

Match priority:

1. stable identifiers;
2. validated canonical identity and contract;
3. explicit, hash-bound input resolution for an allocation;
4. amount/date/text similarity, candidate-only.

An `APPROVED` link is an evidence-qualified data link. It is not company approval. It requires hash-bound evidence and cannot use the similarity method.

Lifecycle compatibility is explicit:

- contract value → billed: `INVOICES`;
- billed → recognized revenue: `POSTS_TO_GL`;
- commitment → posted actual: `FULFILLS_COMMITMENT`;
- accrual → posted actual: `ACCRUAL_FOR`;
- posted cost → paid cash, or billed/recognized revenue → collected cash: `SETTLES`;
- original → opposite-signed reversal in the same stage: `REVERSES`.

Unresolved or cross-scope allocation is permitted only for `SETTLES`, `ALLOCATES_TO` or `TRANSFERRED_BETWEEN`, with an input-resolution reference and hash evidence. Other scope mismatches block.

## Allocation and match groups

- Store source amounts as signed integer minor units.
- Store allocation edges as nonnegative absolute minor-unit magnitudes.
- Require `sum(source allocations) = sum(target allocations)` for each link.
- Support one-to-many, many-to-one and several links forming one connected same-axis match group.
- Enforce each event's capacity once per relation axis. The same event may appear on different axes without cross-axis collision.
- Compute completion across the connected match group, not only per individual edge. This prevents a pair of explicit 60/40 links from being falsely blocked when together they allocate 100%.
- A positive group residual remains `PENDING_RESIDUAL`. Never spread, plug or infer the residual.
- Same-axis over-allocation blocks even when every individual link is locally valid.

## Reversal and supersession

- Keep both original and reversal events.
- `REVERSES` must be one-to-one, bind the original event ID, have equal absolute allocation, preserve opposite signs and produce zero signed net.
- A credit, refund or reduction retains its evidence-governed source sign and lifecycle stage.
- `SUPERSEDES` is nonfinancial, uses explicit version resolution and preserves the superseded version.

## Source conservation and dual channels

Every item occupies exactly one pool:

```text
source_control_amount
= included_amount
+ excluded_amount
+ pending_amount
+ parse_error_amount
```

Run the same equation for signed amounts and absolute magnitudes. Both deltas must be zero minor units.

Independent included aggregation:

- Channel A directly iterates included items.
- Channel B separately accumulates source control and subtracts excluded, pending and parse-error pools.
- Signed and absolute Channel A minus Channel B deltas must both be zero.

Pending or parse-error pools may coexist with a mathematically passing conservation report, but execution remains `BLOCKED`. Event-level R7 pass does not imply named-Metric or workbook readiness.

## Required private outputs for a later integrated run

- relation events and identity bindings;
- dedup decisions, candidate pairs and review tasks;
- typed event links and connected match-group controls;
- source conservation and dual-channel report;
- blockers and explicit residual pools;
- `output_index.json` and a human-readable absolute output locator;
- immutable run manifest and detached seal when the later run-artifact contract is active.

Public summaries contain only aggregate counts, registered statuses and control deltas. They do not contain raw names, paths, document IDs, source IDs, event IDs, hashes or private evidence.

## Stop conditions

Stop and return `BLOCKED` when any of the following occurs:

- candidate-pair budget exceeded;
- same-key changed version lacks an exact resolution;
- business equivalence or ambiguous link lacks qualified evidence;
- cross-scope allocation lacks an allowed relation and input resolution;
- lifecycle type and relation type conflict;
- source/target allocation differs by any minor unit;
- same-axis capacity is exceeded;
- connected match-group residual remains without an explicit downstream pending scope;
- source conservation or either independent aggregation channel has a nonzero delta;
- any R7 object claims final Metric inclusion or company approval state.
