# Auto AU-040 exact-byte schema promotion handoff

- State: `DRAFT_NON_ACTIVE_SCHEMA_PROMOTED`
- Phase: `AUTO_SCHEMA_PROMOTION_TO_FINAL_PATHS`
- Phase base: `25a955728fd18249d9b0ae7bc13428a5a69f259c`
- Current trusted candidate Git object:
  `sha1:899a4374bc02f5e18444fea7404864df7b118adf`
- Current trusted candidate bundle digest:
  `2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5`
- Current candidate size: `29 schemas / 5 policies`
- Promotion interface:
  `CodexSkills/registry/auto/schemas/public-v2/promotion-interface.json`
- Promotion interface raw SHA-256:
  `65c2e83bb2491d1cb3059767cf1705fc7541bd7e97449f33a51ba17a04f5e595`
- Auto runtime interface raw SHA-256:
  `b1da80b2bba552f391863ec82d1c6ff18cedc6c370b55b8ddd81796c112c01b1`

## Completed in this phase

Auto consumed the independently verified Mechanism semantic/policy acceptance
interface:

```text
path=CodexSkills/governance/au040/semantic-policy-acceptance.json
raw_sha256=3385df5975859ef0774d2086a8aa28a0336307e3343e7832eec9e2f024504fda
verified_git_object=sha1:d4d488ab6f1720f3a837b071caf5c9cf6ac5f8e6
status=DRAFT_NON_ACTIVE_SEMANTIC_POLICY_ACCEPTED
```

The four accepted Auto schemas were copied byte-for-byte from the immutable
`transport-draft/` source paths into the isolated stable sibling root
`CodexSkills/registry/auto/schemas/public-v2/`. The draft interface remains
byte-identical at raw SHA-256
`aa4d1b174d45b87424b81f0896c7a594e72f24bfdc16e4128c133ed543fb3831`;
it was not rewritten after Mechanism bound it.

| Schema | Raw SHA-256 | Canonical schema SHA-256 | Self pointer |
| --- | --- | --- | --- |
| `daily-run-shard-manifest:v1` | `5a38f1f4844b348f376a4c0633c16e7e4162df503c2403ac22e11a113bc1c820` | `e9214388da78376da47770934454d65a57659d1dde33fa0cb4e36b79e4665337` | `/manifest_digest` |
| `publication-manifest:v2` | `ef0848afc6dbe82c33df87c8d550de9eeef591af4a50b86e191aefd0dff7de7e` | `e7f8c4dd623379052829a21e3fcae77a98f14b3da1d79bb8f1d416f828063346` | `/manifest_digest` |
| `retention-receipt:v3` | `ddb464fe6a381580af486df25a85c4750b1743289cb631732f77d36944c8b215` | `81435881fbc5e1ced14975edbedee63ca6555674db36f906bdfdee20eb317c45` | `/receipt_digest` |
| `run-event-index-entry:v1` | `dd9fa5c6a2163b38c37972e06cfb0b8b7990f5a8ef335a1c7559aeceef214014` | `27663e9da3d9511cf9a03d1fe6f4b3779b1bbdab8f2f8adb94a274b8653a1433` | `/index_entry_digest` |

The deterministic promotion builder and validator prove:

- every promoted file is exact-byte equal to its accepted draft source;
- every raw and canonical digest, `$id`, self pointer, relationship, and final
  path matches both source interfaces;
- final paths are under `schemas/public-v2/` and contain no `draft` component;
- the current recursive `schemas/public/` loader still sees exactly the
  current candidate set;
- the current candidate remains 29/5 and names neither draft nor promoted
  paths;
- the accepted offline target closes at exactly 31 schemas / five policies;
- unknown schema URNs and any interface, guard-set, or byte drift fail closed.

The promotion interface acknowledges all seven required Mechanism production
semantic guards:

```text
CANONICAL_BYTES_PHYSICAL_DIGEST_CLOSURE
INDEX_EVENT_MANIFEST_CLOSURE
MANIFEST_PART_IMMUTABILITY
MANIFEST_PREDECESSOR_EXACT_CHAIN
PRUNE_TRANSACTION_ARTIFACT_SET_CLOSURE
RETENTION_ANCHOR_EXACT_365D
SHARD_TRANSACTION_ARTIFACT_SET_CLOSURE
```

The accepted future policy material remains Mechanism-owned:

- `public-value-policy:v2`
  `cff871b00dec9d33ba6bd879e02b7039cef57d11e35bdc4c57a80d4d3ea519d4`
- `retention-policy:v3`
  `bcad1e50a847e040d1350ca2fd977503b4ae642deabd727266e9dbbd26acb7ce`
- `public-value-policy` schema v2
  `16a233cab9f403b25da933414156f0f776a76c06518b792a0ff9691d813793aa`
- `retention-policy` schema v3
  `ad5637fad9600941db02ce3cc5f3078d9cc96730603407ff0c019588a32d0ea3`

## Boundaries still closed

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

This phase did not create or modify a candidate bundle, consumer, activation
control, runtime schema loader, writer, publisher, queue, retention executor,
`CodexSkills/VERSION`, activation instance, state root, Gmail notification,
shard, manifest instance, index instance, automation, or watermark. It did not
call the verifier, perform historical validation/backfill, add a time window,
restart the App, or touch any paused automation.

## Next exact action

Mechanism independently fetches and reads back this promotion, then performs
only `MECHANISM_FINAL_31_5_CANDIDATE_CONSUMER_CONTROL`. That phase may bind the
stable promoted paths plus the accepted Mechanism v2/v3 policy material into a
new 31/5 candidate and synchronously rebuild the consumer/control tuples. Auto
runtime integration must wait for the exact new bundle tuple from that
independent phase.

The Owner must still resolve 04:15 versus 05:30 explicitly and provision the
repo-external owner-only state root before any later Gmail readiness or M0c-B
run. Activation and canonical publication remain forbidden.
