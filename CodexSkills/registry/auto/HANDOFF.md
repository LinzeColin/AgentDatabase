# Auto consumer-first trust sync handoff

- State: `DRAFT_NON_ACTIVE`
- Phase: `AUTO_CONSUMER_FIRST_TRUST_SYNC`
- Implementation baseline:
  `sha1:2177986e897fdc50a7273f099a1305b21de2096b`
- Candidate Git object:
  `sha1:899a4374bc02f5e18444fea7404864df7b118adf`
- Candidate bundle digest:
  `2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5`
- Verified M0c-A Git object:
  `sha1:3a0b8222cf52d6a35f31986c411ac98daed06c5c`
- M0c-A control interface raw SHA-256:
  `70b4e8c8ab47db541c90bbc6ebf092a483ca776c07b84b939b5a9b0be783e5c2`
- Consumer interface:
  `OpenAIDatabase/config/evaluation/skill_run_consumer.json`
- Consumer interface raw SHA-256:
  `750a374f5eb20497baab79305dc31248a7495cf3c7dee827cad19d13e08e2082`
- Auto runtime interface:
  `CodexSkills/registry/auto/runtime-interface.json`
- Auto runtime interface raw SHA-256:
  `783eadab846c2481088c41dd1cce19f95d8568021cf7e0f9ab9d5a094727e649`

## Completed in this phase

- The Mechanism-owned consumer repin at `2177986e...` was independently
  fetched and read back before this Auto phase started. Its exact three-path
  change did not modify Auto-owned files or `CodexSkills/VERSION`.
- The consumer now binds the relocated candidate object `899a4374...`, bundle
  digest `2704ed79...`, canonical manifest path, and `CANDIDATE` mode. Its
  direct CLI returns `PASS` with no errors while keeping canonical publication
  disabled.
- The Auto runtime-interface builder now reads the exact consumer bytes,
  rejects duplicate JSON keys, pins the raw SHA-256, and verifies status,
  owner plane, trust tuple, and publication gates. Checkout drift cannot be
  represented as a completed consumer-first gate.
- `consumer_first_gate_satisfied=true` means only that the consumer-first
  trust tuple and fail-closed parser are present. It does not imply ACTIVE
  trust, repository shard permission, AU-040, BOUND reference resolution,
  Gmail readiness, M0c-B, or canonical publication.

## Validation evidence

- Relocated Auto unittest: `106/106 PASS`.
- Mechanism unittest: `42/42 PASS`.
- OpenAIDatabase consumer and architecture: `20/20 PASS`.
- Seeded fault/privacy: `92/92 PASS` for seed `271828`; `92/92 PASS` for
  seed `314159`.
- Mechanism draft, candidate bundle, activation control, Auto schemas, and
  Auto runtime interface are byte-equivalent.
- Trusted candidate bundle: `29 schemas / 5 policies PASS`.
- Activation control: two bootstrap schemas over the pinned `29/5` candidate
  `PASS`.
- Candidate runtime preflight: Python/dependency/vendor/offline Registry
  `PASS`.
- Consumer CLI: `PASS`, errors empty, canonical publication false.
- Python 3.9 AST, diff-check, no-VERSION, and Auto-owner path boundary checks:
  `PASS`.
- Immutable Task Packs were read for authority but were not historically
  rerun.

## Unresolved schedule authority

The current runtime and frozen cross-pack policy implement
Australia/Sydney 04:15. The active Auto goal contains
`Australia/Sydney 每日 05:30 运行`, but it does not explicitly say that it
supersedes or revokes the earlier Owner-locked 04:15 value. The immutable
v0.0.0.2 Task Packs require daily, DST-safe operation but do not specify an
exact clock time. The machine interface therefore keeps
`schedule_authority_conflict_detected=true`,
`schedule_authority_resolved=false`, and `schedule_complete=false`. This phase
does not modify schedule code, policy, tests, prompt, or automation.

## AU-040 read-only authority ruling

Both immutable Task Packs require bounded daily JSONL shards plus a manifest;
the Auto specification places both under `skills_runs`. The current consumer
accepts only the root README and
`YYYY/MM/DD/part-NNNN.jsonl`, so any manifest path is rejected. The shared
`publication-manifest:v1` is transaction-level and does not establish a daily
manifest filename/path or JSONL record-container semantics.

Mechanism Authority Audit Revision 6 resolved the design direction without a
repository change:

- immutable parts remain
  `YYYY/MM/DD/part-NNNN.jsonl`;
- append-only daily revisions become
  `YYYY/MM/DD/manifest-NNNN.json`;
- the proposed Auto-owned public schema is
  `daily-run-shard-manifest:v1`, distinct from transaction
  `publication-manifest:v1`;
- JSONL publication requires an explicit per-line serialization mode and
  bounded streaming schema/privacy/digest validation;
- part numbers are never reused, manifest entries remain contiguous, and
  physical part gaps are permitted only after an exact receipt-backed prune;
- exact affected-record retention evidence plus long-lived idempotency,
  correction, and dedupe index readiness are additional canonical gates.

Revision 6 is read-only and has no repository SHA or interface digest.
Consequently, `au_040_manifest_contract_resolved=false`,
`au_040_consumer_manifest_path_contract_present=false`, and
`au_040_daily_jsonl_shard_complete=false`. This phase records the frozen
direction as `READ_ONLY_REVISION_6_NOT_REPOSITORY_BOUND`; it does not
reinterpret a schema, replace the 29-schema candidate, or generate a shard.

## External readiness remains closed

`SKILLOPS_STATE_ROOT` is absent in the controlled runtime. State-root
permissions, recipient mapping, Gmail config, OAuth scopes, authenticated
profile binding, query endpoint readiness, and real-message metadata readback
remain `UNKNOWN/NOT_READY`. No Gmail API or network request was made.
`external_gmail_ready_gate_satisfied=false` and `m0c_b_permitted=false`.

## Explicitly not done

This phase does not create `CodexSkills/VERSION`, an activation intent,
notification receipt, settlement, ACTIVE manifest, production state root,
watermark, daily shard, canonical data, or automation change. It does not
send email, run M0c-B, call the verifier, run historical Task Pack validation,
restart the App, introduce a time window, backfill history, or touch any
paused automation.

## Next exact action

The next independent Auto phase drafts only the Auto-owned, non-active AU-040
transport schemas and interfaces frozen by Revision 6. It must keep
`repository_bound=false`, AU-040 false, and the current 29-schema candidate
unchanged. A later Mechanism phase owns candidate-bundle replacement and
consumer/retention/reference closure; only then may Auto integrate the exact
new bundle.

Separately, the Owner must explicitly choose 04:15 or 05:30 before either
plane changes the schedule. The Owner must also provision the repo-external
`0700` state root and exact `0600` notification contracts before a controlled
no-send Gmail readiness gate can run. M0c-B remains forbidden until every
required gate is directly READY.
