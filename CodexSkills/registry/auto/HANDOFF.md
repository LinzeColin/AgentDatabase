# Auto exact-bundle integration handoff

- State: `DRAFT_NON_ACTIVE`
- Phase: `AUTO_EXACT_BUNDLE_INTEGRATION`
- Phase base/control object:
  `66d5bafadca508cad825b4ce49a42e81e8b66ef7`
- Final candidate Git object:
  `sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5`
- Final candidate bundle digest:
  `36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e`
- Final candidate manifest raw SHA-256:
  `66ad125629cab71739ff2bc266219f995f7a45998936ca720c6db678ee77e65a`
- Final candidate size: `31 schemas / 5 policies`
- Consumer V2 Git object:
  `sha1:91a12e48351be3ee05ec23ef61aec81056b02014`
- Consumer raw SHA-256:
  `189a47300fc1aa6012e87feb6184833cb717cdbe2b9dc9be6db89197f579939c`
- Current control raw SHA-256:
  `86e4d625bdab87261a39c949883d410822e25e0222dbab6a333d171ce420c614`
- Auto runtime interface raw SHA-256:
  `09af0c00273825e90a489f413a2f0bb6995042e5b4eea17973ce7582eab66340`

## Completed in this phase

The production bootstrap now requires two caller-supplied, repo-external trust
tuples on every preflight and orchestrator call:

1. the candidate content tuple (`5ee37d7...`, `36f0c66...`, canonical manifest
   path, `CANDIDATE`);
2. the control tuple (`66d5baf...`, `86e4d62...`, canonical control path,
   `DRAFT_NON_ACTIVE_CONTROL`).

The candidate tuple selects all manifest, schema, policy, and canonicalization
vector bytes from the candidate object. The control tuple selects the local
Mechanism validation/control runtime and the control interface bytes. The
checkout's self-report, caller booleans, caller digest maps, or the control's
historical source-runtime pointer cannot replace either trust root.

The immutable legacy 29/5 loader remains available only for historical draft
and promotion evidence. Production bootstrap requires the exact final 31/5
profile, composes the four private Auto schemas outside the shared bundle, and
rejects the historical tuple or any hybrid profile. Public-value scanning now
selects the trusted v2 policy for the final profile.

`runtime_preflight.py`, `notification_transport_cli.py`,
`activation_handshake_cli.py`, and `SkillOpsOrchestrator` all consume both
external tuples. Activation control loads the 31/5 bundle plus the two
bundle-external activation schemas. Retention's managed-raw path uses
`retention-policy:v3` and `retention-receipt:v3`; GIT current-tree pruning
remains explicitly blocked because the AU-040 runtime writer is not integrated.

The current control truthfully says
`transition_contract.auto_runtime_integration_complete=false`. Therefore:

- read-only final-bundle preflight/shadow proof is available;
- all production state-writing orchestrator and notification/activation
  entrypoints fail with
  `RUNTIME_CONTROL_SYNC_REQUIRED_BEFORE_STATE_WRITE` before state creation;
- the current control's d162/e8d8 transport-runtime pointer is verified only as
  lineage/source evidence and does not self-lock this new Auto runtime.

The deterministic runtime interface independently verifies the exact candidate
A blob, consumer B blob, control C blob, local control runtime, historical
promotion evidence, and all false gates. It reports:

```text
auto_exact_bundle_integration_complete=true
control_observed_auto_runtime_integration_complete=false
runtime_preflight_shadow_permitted=true
runtime_state_write_permitted=false
shared_bundle_schema_count=31
shared_policy_count=5
next_phase=MECHANISM_POST_AUTO_INTEGRATION_CONTROL_SYNC
```

## Boundaries still closed

- `repository_bound=false`;
- `au_040_daily_jsonl_shard_complete=false`;
- AU-040 runtime shard/index/manifest writer is absent;
- publication-manifest:v2 publisher integration is absent;
- `canonical_publication_permitted=false`;
- `external_gmail_ready_gate_satisfied=false`;
- real provider metadata readback remains false;
- `m0c_b_permitted=false`;
- `activation_instance_created=false`;
- `schedule_authority_resolved=false`;
- `schedule_complete=false`.

This phase created no VERSION, state root, Gmail operation, intent, receipt,
settlement, shard, index, daily manifest, publication, watermark, automation,
or App action. It did not call the verifier, replay historical runs, add a
time window, or touch the three PAUSED automations.

## Unrelated baseline failure

The additional broad command-ownership check is not green:

```text
command=/usr/bin/python3 -B OpenAIDatabase/scripts/validate_command_ownership.py --database-dir OpenAIDatabase
error=top-level script entrypoints: expected 84, observed 85
status=FAIL
```

It has the identical error and metrics on exact base C
`66d5bafadca508cad825b4ce49a42e81e8b66ef7` and on this Auto worktree.
This phase changes no `OpenAIDatabase/**` path, so the failure is reported as a
pre-existing broad baseline condition, not as PASS and not as an Auto
regression.

## Next exact action

After ordinary FF-safe push and independent GitHub object readback of this Auto
commit, Mechanism alone performs
`MECHANISM_POST_AUTO_INTEGRATION_CONTROL_SYNC`. It must rebuild/read back a
successor control that binds the new Auto object and runtime-interface raw
SHA-256, then set `auto_runtime_integration_complete=true` without doing
activation, Gmail/state readiness, shard publication, VERSION, automation,
schedule, or verifier work.

The Owner must still resolve 04:15 versus 05:30 explicitly and provision the
repo-external owner-only state root before later Gmail readiness or M0c-B.
