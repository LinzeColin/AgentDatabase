# Mechanism handoff

- State: DRAFT_NON_ACTIVE
- Phase: MECHANISM_AU040_SEMANTIC_POLICY_ACCEPTANCE
- Task Pack authority: immutable CodexSkills-Mechanism-Design-TaskPack-v0.0.0.2
- Protocol: urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1
- SRV candidate: v0.0.0.3
- Candidate manifest: CodexSkills/governance/bundles/schema-bundle-manifest.v1.json
- Candidate bundle digest: 2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5

## Pinned inputs

- Candidate bundle Git object:
  sha1:899a4374bc02f5e18444fea7404864df7b118adf
- Auto runtime baseline Git object:
  sha1:c2fc04ff24b8d8ad72ec14a1cc2b26000ba08f67
- Auto runtime interface raw SHA-256:
  e28040a58d4c68b2493025523982545d8aa80b1faf7961cf03860d735f8cdea2
- Mechanism interface raw SHA-256:
  0f4837d9cec37c845cd5e9e799b5f572944cf8fe2457e8b95f696db3b9c03998
- M0c-A activation control Git object:
  sha1:3a0b8222cf52d6a35f31986c411ac98daed06c5c
- M0c-A activation control interface raw SHA-256:
  70b4e8c8ab47db541c90bbc6ebf092a483ca776c07b84b939b5a9b0be783e5c2

The later Auto Gmail query-capability corrective is not a replacement for the
immutable M0c-A control tuple above. Its verified Git object is
`sha1:befc5b0ee9e7f5157f31a2b6a8809cd118f1b5fd`; the current Auto runtime
interface raw SHA-256 is
`43a30b67903e9f5284f607129b7e3830aa507449552190b5992db770c01299d4`.

## Completed through M0b

- The complete candidate contains exactly 21 Mechanism schemas, eight
  Auto-public schemas, and five Mechanism policies.
- All entries are ASCII-ID sorted, content-addressed with RFC 8785 canonical
  SHA-256, owned by one plane, bound to an exact path, and marked EXACT_ONLY.
- The four Auto-private schemas are excluded from the shared bundle.
- The manifest digest excludes only /bundle_digest. Member and policy digests
  remain covered by the manifest digest.
- The candidate uses exact protocol and bundle-digest compatibility with no
  accepted predecessor bundle.
- The deterministic builder pins both machine-interface byte digests and
  refuses interface drift, ACTIVE VERSION state, member-count drift, path or
  owner mismatch, private-schema inclusion, digest mismatch, and malformed
  public values.
- Local draft loading structurally validates a candidate but returns only the
  21-schema Mechanism draft. It never upgrades repository self-reporting into
  a trusted complete bundle.

## Completed in M0c-A

- A field-level audit proved the existing single-artifact envelope cannot bind
  the complete activation write set, and the existing publisher must not trust
  a caller-supplied verification boolean or digest map.
- `activation-intent:v1` freezes the full planned path set before notification,
  including the exact VERSION bytes and explicit post-provider-derived paths.
- `activation-settlement:v1` is created only after a real `PRE_WRITE` provider
  `SENT` receipt. It binds the exact intent and receipt evidence plus every
  final artifact's physical SHA-256.
- The settlement is a distinguished control artifact and cannot list its own
  physical digest. The final publisher must require request paths equal the
  settlement artifact set plus the settlement path and recompute every byte.
- The Mechanism Handoff may reference the settlement path but cannot embed the
  settlement digest, preventing a handoff/settlement digest cycle.
- Both bootstrap-control schemas are versioned and digest-pinned outside the
  unchanged 29-schema/5-policy candidate bundle. The complete machine interface
  is `CodexSkills/governance/activation/control-interface.json`.
- That control interface and its two schemas gain runtime trust only through an
  external tuple of verified M0c-A Git object, expected raw interface SHA-256,
  canonical interface path, and mode `DRAFT_NON_ACTIVE_CONTROL`; repository
  self-reporting is insufficient.
- The validator loads the 29 schemas and five policies only from the externally
  pinned candidate Git object and trust tuple; a later working-tree change
  cannot silently replace activation semantics.
- Public JSON intent, notification receipt, and settlement bytes are RFC 8785
  JCS UTF-8 with no BOM or trailing newline. Reads traverse descriptor-relative
  `O_NOFOLLOW` gates and reject symlink roots, parents, and files.
- Notification metadata exposes only the conservative public scopes
  `CodexSkills/VERSION` and `CodexSkills/governance`; the intent digest binds
  the exact five-path write set without leaking high-entropy receipt paths.
- Positive, negative, privacy, path, ordering, provider-state, evidence-binding,
  physical-digest, and cycle fixtures are executable offline.

## Completed in consumer-first

- The registry relocation invalidated the prior consumer tuple because its
  historical manifest referenced `CodexSkills/auto/**`, while the unique
  validator now requires the canonical `CodexSkills/registry/auto/**` owner
  paths. The validator fails closed on that old tuple; this repin binds the
  consumer to relocated candidate object
  `sha1:899a4374bc02f5e18444fea7404864df7b118adf` and bundle digest
  `2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5`.
- The sibling task-run validator now enumerates only the four legacy task-run
  categories. It cannot glob or reinterpret recursive SkillOps shards as
  `task_run` rows.
- `OpenAIDatabase/config/evaluation/skill_run_consumer.json` pins the exact
  candidate Git object, bundle digest, manifest path, protocol, schema ID,
  Australia/Sydney shard calendar, RFC 8785 per-line framing, gapless
  `part-NNNN.jsonl` layout, and 20 MiB part budget. Its raw SHA-256 is
  `750a374f5eb20497baab79305dc31248a7495cf3c7dee827cad19d13e08e2082`.
- Consumer bootstrap rejects duplicate keys, invalid I-JSON, untrusted bundle
  IDs, unknown URNs, unsafe roots, symlink/special-file entries, invalid
  dates, direct-root event files, unexpected directories, and every
  unapproved path. Descriptor-relative `O_NOFOLLOW` reads close the config and
  log-tree path race; fixed entry/error budgets bound hostile tree scans.
- `tools/validate_public_run_event.py` applies schema, contextual bundle
  equality, self-digest, public-value scanning, binding surface/role,
  controlled-invocation time/surface, correction, and token-measurement
  semantics without importing Auto runtime code or modifying M0c-A-pinned
  validator bytes.
- The canonical repository run root still contains only its README. Synthetic
  final-layout records can be validated, but repository shards remain
  unconditionally blocked.
- OpenAIDatabase lifecycle, minimum validation, harness, README, and regression
  tests now identify `skills_runs` as a separate consumer surface.

## Completed in AU-040 semantic/policy acceptance

- Auto's four transport schemas are accepted at their exact draft byte
  digests and self-digest pointers; promotion may only copy those bytes into
  `CodexSkills/registry/auto/schemas/public-v2/`.
- Public-value policy v1 is not mutated. Versioned
  `public-value-policy:v2` / `public-value:v2` add exactly ten digest field
  names while preserving the detector, forbidden-field and repo-external
  recipient contracts. Generic digest aliases, malformed values and
  low-entropy sensitive-value hashes remain forbidden.
- Retention policy v3 freezes 365 elapsed 24-hour days from
  `first_published_at`, retention at the exact boundary, strict eligibility
  only after the boundary, a 24-hour audit deadline whose equality is on time,
  and truthful gap evidence after a breach. Host/App unavailability remains a
  recorded limitation, never a hard deadline guarantee.
- Seven Mechanism-owned semantic gates close constraints JSON Schema cannot
  establish alone: exact canonical physical bytes, index/event/manifest
  linkage, immutable existing part metadata, exact append-only predecessor
  revisions, paired new part/index/manifest publication, and paired
  delete/retention-receipt/new-manifest publication.
- Retention receipts use the versioned daily-tree pattern
  `YYYY/MM/DD/retention-receipt-NNNN.json`; they are public JCS objects and
  must be in the same RUN_LOG transaction as the deletion and new manifest.
- The accepted target is exactly 31 schemas/five policies. The current
  candidate remains exactly 29/five and no bundle, consumer, control,
  VERSION, runtime state, shard, receipt instance or canonical publication was
  materialized.
- Machine handoff:
  `CodexSkills/governance/au040/semantic-policy-acceptance.json`.

## Explicitly not active / current capability state

M0c-A does not create `CodexSkills/VERSION`, an ACTIVE manifest, activation
intent instance, notification receipt, settlement instance, canonical data,
runtime watermark, or publication authority. It sends no email. The relocated
candidate remains deterministic and is trusted only when a caller supplies
the repo-external tuple of verified M0b Git object, exact candidate digest,
canonical manifest path, and mode CANDIDATE.

The production Gmail implementation and its deterministic no-send query
capability probe now exist. Runtime readiness of the repo-external state root,
recipient mapping, OAuth credential, authenticated profile binding, and query
endpoint remains `UNKNOWN` because `SKILLOPS_STATE_ROOT` is not provisioned in
the controlled runtime environment. Real-message metadata readback also
remains unproved until M0c-B performs an actual send and exact provider
readback. A connected Gmail App is not a substitute for that production trust
root. Missing external state fails closed.

This phase still does not claim AU-040. The shared v0.0.0.3 candidate has individual
`public-run-event:v2` records and a transaction-level
`publication-manifest:v1`, but no proven daily JSONL shard/manifest payload
contract. BOUND events also remain blocked from canonical publication until
the Registry-backed exact reference resolver lands.

## Next exact action

Auto may run only `AUTO_SCHEMA_PROMOTION_TO_FINAL_PATHS`: copy the four
accepted schema byte streams exactly into the frozen `public-v2/` paths,
acknowledge the seven Mechanism semantic guards, and keep the candidate,
consumer, control, runtime integration, activation and canonical publication
unchanged. Mechanism may build the final 31/5 candidate and update the
consumer/control only after that promotion is independently read back.

The exact daily schedule authority remains unresolved: the directly frozen
contract says 04:15 while a later Auto goal says 05:30 without explicitly
overriding it. Neither time may be presented as final until Owner resolves the
precedence. Gmail/state readiness and M0c-B also remain false.
