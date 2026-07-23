# Auto AU-040 transport schema draft handoff

- State: `DRAFT_NON_ACTIVE`
- Phase: `AUTO_AU040_TRANSPORT_SCHEMA_DRAFT`
- Phase base:
  `a461de2dc3583456135260700c00bd212f3e65b6`
- Current trusted candidate Git object:
  `sha1:899a4374bc02f5e18444fea7404864df7b118adf`
- Current trusted candidate bundle digest:
  `2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5`
- Current candidate size: `29 schemas / 5 policies`
- Transport draft interface:
  `CodexSkills/registry/auto/transport-draft/draft-interface.json`
- Transport draft interface raw SHA-256:
  `aa4d1b174d45b87424b81f0896c7a594e72f24bfdc16e4128c133ed543fb3831`
- Auto runtime interface raw SHA-256:
  `91e184f37e9b166b78847b654f17447e67df6bc92db66713e5feac4634e00127`

## Completed in this phase

This phase adds four Auto-owned transport schema proposals and a dedicated
offline semantic validator. The proposals are isolated from the current
candidate under `transport-draft/`; they are not loaded by the runtime or the
current recursive public-schema loader.

The proposed active shared set targets exactly 31 schemas and five policies:

- replace `publication-manifest:v1` with `publication-manifest:v2`;
- replace `retention-receipt:v2` with `retention-receipt:v3`;
- add `daily-run-shard-manifest:v1`;
- add `run-event-index-entry:v1`.

The current `899a4374...` / `2704ed79...` candidate remains exactly 29/5 and
byte-equivalent. No candidate manifest, control interface, Mechanism file, or
OpenAIDatabase file changed.

For schema validation only, the draft Registry composes the four proposals
with the current five policies. This is not a claim that the target policy set
is complete: `retention-policy:v3` is absent and must replace v2 only after
Mechanism acceptance. The machine interface records
`retention_policy_v3_present=false`.

### Exact draft schema evidence

| Schema | Self pointer | Canonical schema SHA-256 |
| --- | --- | --- |
| `daily-run-shard-manifest:v1` | `/manifest_digest` | `e9214388da78376da47770934454d65a57659d1dde33fa0cb4e36b79e4665337` |
| `publication-manifest:v2` | `/manifest_digest` | `e7f8c4dd623379052829a21e3fcae77a98f14b3da1d79bb8f1d416f828063346` |
| `retention-receipt:v3` | `/receipt_digest` | `81435881fbc5e1ced14975edbedee63ca6555674db36f906bdfdee20eb317c45` |
| `run-event-index-entry:v1` | `/index_entry_digest` | `27663e9da3d9511cf9a03d1fe6f4b3779b1bbdab8f2f8adb94a274b8653a1433` |

The daily manifest binds Sydney local date, per-line JCS/LF framing, a 20 MiB
part limit, append-only manifest revisions, contiguous non-reused part
numbers, exact shard and persistent-index evidence, active/pruned state,
receipt-backed pruning, and aggregate arithmetic. Semantic tree validation
requires every ACTIVE shard, forbids every PRUNED shard, and requires every
paired index to remain.

The event index is per-line JCS. It retains public-safe UID/digest/time/part/
line evidence and the exact UID+digest supersession pair for a
`BINDING_CORRECTION`. Group validation requires contiguous line numbers,
`(occurred_at,event_uid)` order, exact part closure, dedupe consistency, and an
exact known correction target.

Publication manifest v2 uses explicit `PUT|DELETE` operations. PUT binds new
exact bytes and either object-JCS or per-line-JCS serialization. DELETE binds
prior exact bytes and has no payload or new digest. Semantic routing rejects
whole JSONL treated as one object, unlisted deletions, and path/schema/
operation/serialization mismatches.

Retention receipt v3 exposes ordered exact public artifact evidence only for
`GIT_CURRENT_TREE + PRUNE_CURRENT_TREE`. Aggregate count and bytes must equal
the item list, each retained index must pair with the removed part, and
`executed_at` must be strictly greater than every `retention_not_before`.
Each affected item binds
`prune_deadline_at = retention_not_before + 24h`. The root breach flag and
fixed `GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH` gap code are recomputed from
`executed_at`; equality with the deadline is on time, while any later instant
is a truthful breach.
`MANAGED_RAW` remains aggregate-only. The receipt has no new-manifest digest;
the later daily manifest may reference the receipt in one direction.

## Public-value policy delta

The existing Mechanism public-value policy was not modified. The current
scanner was run against every legal fixture and blocked exactly these sorted
digest-field names:

```text
first_event_digest
index_digest
index_entry_digest
last_event_digest
previous_manifest_digest
prior_artifact_digest
prior_daily_manifest_digest
retained_index_digest
retention_receipt_digest
shard_digest
```

The draft validator only applies this exact delta to an in-memory policy copy
after proving the current scanner's fail-closed result. Mechanism must accept
or reject the delta in its own independent phase. No generic renaming or
scanner bypass is permitted.

Mechanism must also provide `retention-policy:v3` with strict
`now > retention_not_before`, retained boundary, 24-hour prune deadline,
active-tree-only semantics, and persistent index/dedupe aggregate retention.

## Loader isolation and promotion guard

`transport-draft/` is never a valid candidate member path. Every schema entry
binds both its draft path and one proposed canonical path under:

```text
CodexSkills/registry/auto/schemas/public-v2/
```

The sibling root is mandatory because the current loader recursively scans
`CodexSkills/registry/auto/schemas/public/` and requires the exact 29-schema
set. The machine interface therefore states:

- `promotion_required_before_candidate_materialization=true`;
- `draft_paths_forbidden_in_candidate_manifest=true`;
- `proposed_paths_visible_to_current_loader=false`.

The ownership-safe sequence is:

1. Auto transport schema draft — complete in this phase.
2. Mechanism semantic/policy acceptance without bundle materialization.
3. Auto promotion of the accepted exact schema bytes to `schemas/public-v2/`.
4. Mechanism final 31/5 candidate, consumer, and control materialization.
5. Auto exact-bundle integration.

Mechanism must not create an intermediate candidate that names the draft
paths.

## Validation evidence

- Auto unittest: `131/131 PASS`.
- New transport contract tests: `25/25 PASS`.
- Mechanism unittest: `42/42 PASS`.
- OpenAIDatabase consumer and architecture: `20/20 PASS`.
- Seeded runtime fault/privacy:
  - seed `271828`: `92/92 PASS`;
  - seed `314159`: `92/92 PASS`.
- Existing Mechanism draft, current 29/5 candidate, and activation control:
  byte-equivalent and valid.
- Existing Auto schemas and runtime interface: byte-equivalent.
- Transport draft builder: byte-equivalent.
- Draft offline Registry: `31 schemas + current 5 policies PASS`;
  target `retention-policy:v3` remains absent/pending.
- Current trusted candidate: `29 schemas / 5 policies PASS`.
- Candidate runtime preflight: `PASS`.
- Consumer CLI: `PASS`, errors empty, canonical publication false.
- Duplicate-key, I-JSON, RFC 8785 JCS, self pointer, context digest,
  conditionals, arithmetic, ordering, Sydney date, retention boundary, privacy,
  path/operation, and JSONL LF framing gates: `PASS`.
- The verifier and historical Task Pack validation were not run.

## Still false / not performed

- `repository_bound=false`;
- `au_040_complete=false`;
- `au_040_manifest_contract_resolved=false`;
- `au_040_consumer_manifest_path_contract_present=false`;
- `au_040_daily_jsonl_shard_complete=false`;
- `canonical_publication_permitted=false`;
- `external_gmail_ready_gate_satisfied=false`;
- `m0c_b_permitted=false`;
- `schedule_authority_resolved=false`;
- `schedule_complete=false`.

This phase did not create or modify a runtime writer, publisher, queue,
retention executor, candidate bundle, control tuple, consumer, `VERSION`,
activation instance, state root, shard, manifest instance, index instance,
notification, automation, or watermark. It made no Gmail or other network API
request, did not call the verifier, did not backfill history, did not add a
time window, did not restart the App, and did not touch any paused automation.

## Next exact action

Mechanism independently fetches and reads back this phase, then performs only
`MECHANISM_AU040_SEMANTIC_POLICY_ACCEPTANCE`. That run may accept/reject the
four exact schema bytes, the ten-field public-value allowlist delta, and the
future retention-policy v3 requirements. It must not yet materialize a new
candidate, consumer, or activation control tuple.

Separately, the Owner must explicitly choose 04:15 or 05:30 before either
plane changes the schedule. The Owner must provision the repo-external `0700`
state root and exact `0600` notification contracts before a controlled no-send
Gmail readiness run. M0c-B remains forbidden.
